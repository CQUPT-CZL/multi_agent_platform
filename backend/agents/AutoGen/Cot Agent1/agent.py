import os
import json
import asyncio
from typing import List, Dict, Any

import autogen
from agents.base_agent import BaseAgent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import StructuredTool

class AutoGenCoTAgent(BaseAgent):
    """
    使用 AutoGen 的 GroupChat 模式，实现一个可以根据任务复杂度自适应调整流程的多 Agent 工作流。
    """

    @property
    def framework(self) -> str:
        return "AutoGen"

    @property
    def name(self) -> str:
        return "autogen_cot_agent_smart"

    @property
    def display_name(self) -> str:
        return "使用AutoGen群聊模式生成CoT(智能路由)"

    @property
    def description(self) -> str:
        return "可根据任务复杂度自适应调整流程，高效处理简单和复杂问题。"

    def _load_mcp_config(self) -> Dict[str, Any]:
        """从 config.json 文件加载 MCP 配置"""
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
            config_path = os.path.join(project_root, "frontend", "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ 成功从 {config_path} 加载 MCP 配置")
                return config
            else:
                print(f"⚠️ 配置文件不存在: {config_path}，使用默认配置")
                return {}
        except Exception as e:
            print(f"❌ 加载 MCP 配置失败: {e}，使用默认配置")
            return {}

    async def run(self, message: List[Dict[str, Any]], model: str, conversation_id: str) -> str:
        """执行 AutoGen Agent 的任务。"""
        print(f"--- Running AutoGen Smart GroupChat Agent for conversation: {conversation_id} ---")
        
        try:
            user_question = message[-1]["content"]
            
            mcp_config = self._load_mcp_config()
            if not mcp_config:
                return "❌ 没有找到有效的 MCP 配置，请在前端界面配置 MCP 工具后再试。"
            
            print(f"📋 当前 MCP 配置: {list(mcp_config.keys())}")
            client = MultiServerMCPClient(mcp_config)
            
            langchain_tools: List[StructuredTool] = []
            try:
                print("🔎 正在尝试从 MCP 服务器加载工具...")
                langchain_tools = await client.get_tools()
                if langchain_tools:
                    print(f"✅ 成功加载 {len(langchain_tools)} 个工具。")
            except Exception as e:
                print(f"\n⚠️  警告：无法从 MCP 服务器加载工具！错误: {e}\n")

            # --- 1. 配置 LLM ---
            llm_config = {
                "model": os.getenv("MODEL", model),
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": os.getenv("OPENAI_API_BASE")
            }
            config_list = [llm_config]

            # --- 2. 定义专家 Agents ---
            analyzer = autogen.AssistantAgent(name="Problem_Analysis_Expert", system_message="你是一个问题分析专家 🧐。", llm_config={"config_list": config_list})
            planner = autogen.AssistantAgent(name="Planning_Expert", system_message="你是一个计划制定专家 📝。", llm_config={"config_list": config_list})
            executor = autogen.AssistantAgent(name="Execution_Expert", system_message="你是一个计划执行专家 🛠️。请使用工具执行计划。", llm_config={"config_list": config_list})
            integrator = autogen.AssistantAgent(name="Integration_Expert", system_message="你是一个整合专家 ✍️。请整合信息并提供最终答案。完成后，请只回复 'TERMINATE'。", llm_config={"config_list": config_list})

            # --- 3. 定义用户代理 ---
            user_proxy = autogen.UserProxyAgent(
                name="User_Proxy",
                human_input_mode="NEVER",
                is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
                code_execution_config=False,
            )

            # --- 4. 注册工具 ---
            if langchain_tools:
                tool_map = {tool.name: tool for tool in langchain_tools}
                async def execute_mcp_tool(tool_name: str, **kwargs: Any) -> Any:
                    print(f"--- 正在执行工具: {tool_name}，参数: {kwargs} ---")
                    if tool_name not in tool_map: return f"错误：未找到工具 '{tool_name}'。"
                    try:
                        return await tool_map[tool_name].ainvoke(kwargs)
                    except Exception as e:
                        return f"执行工具 '{tool_name}' 时出错: {e}"
                
                autogen.register_function(
                    execute_mcp_tool,
                    caller=executor,
                    executor=user_proxy,
                    name="execute_mcp_tool",
                    description="执行一个由MCP提供的工具来完成任务。",
                )

            # --- 5. 设置智能群聊和管理器 ---
            groupchat = autogen.GroupChat(
                agents=[user_proxy, analyzer, planner, executor, integrator],
                messages=[],
                max_round=15,
                # [MODIFIED] 设置为 "auto"，允许管理器自由选择下一个发言者
                speaker_selection_method="round_robin"
            )
            
            # [MODIFIED] 赋予管理器更智能的系统指令
            manager = autogen.GroupChatManager(
                groupchat=groupchat,
                llm_config={"config_list": config_list},
                system_message="""你是一个智能的团队总监 👨‍💼。你的任务是协调一个专家团队，高效地回答用户的问题。

                **你的决策流程如下：**

                1.  **评估请求**：首先，仔细阅读用户的初始请求。

                2.  **决策路由**：
                    * **如果请求是简单问题**（例如，打招呼、常识性问题、可以直接回答的查询），请**直接选择【Integration_Expert】**来提供答案，以节省时间和资源。
                    * **如果请求是复杂任务**（需要分析、制定多步骤计划、并可能需要使用工具），请严格按照以下顺序引导对话：
                        a.  **Problem_Analysis_Expert** (进行分析)
                        b.  **Planning_Expert** (制定计划)
                        c.  **Execution_Expert** (执行计划)
                        d.  **Integration_Expert** (整合并给出最终答案)
                
                请在每次选择下一个发言人时，明确说明你的理由。
                对话的最终目标是让【Integration_Expert】给出完整答复并以 'TERMINATE' 结束。
                """
            )

            # --- 6. 启动对话 ---
            print("🚀 Starting AutoGen Smart GroupChat Workflow...")
            await user_proxy.a_initiate_chat(
                manager,
                message=user_question,
            )
            print("✅ Workflow finished.")
            
            # --- 7. 提取最终答案 ---
            print(groupchat.messages)
            final_answer = groupchat.messages[-1]["content"]
            if final_answer.endswith("TERMINATE"):
                final_answer = groupchat.messages[-2]["content"]
            
            print("Final Response:", final_answer)
            return final_answer

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ AutoGen Agent 执行失败！\n\n**错误信息**: {str(e)}"
