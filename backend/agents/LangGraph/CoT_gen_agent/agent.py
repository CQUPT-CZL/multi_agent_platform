import os
import json
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph_supervisor.handoff import create_forward_message_tool
from langgraph_supervisor import create_supervisor
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

class LangGraphCoTAgent(BaseAgent):
    """
    讲一个问题生成CoT长思维链
    """

    @property
    def framework(self) -> str:
        return "LangGraph"

    @property
    def name(self) -> str:
        return "langgraph_cot_agent"

    @property
    def display_name(self) -> str:
        return "使用supervisor模式生成CoT"

    @property
    def description(self) -> str:
        return "使用supervisor模式生成CoT长思维链数据"

    def _load_mcp_config(self) -> Dict[str, Any]:
        """
        从 config.json 文件加载 MCP 配置
        """
        try:
            # 获取项目根目录下的 frontend/config.json 路径
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
        """
        执行 LangGraph Agent 的任务。
        """
        print(f"--- Running LangGraph MCP Agent for conversation: {conversation_id} ---")
        
        try:
            user_question = message[-1]["content"]

            # 从 config.json 加载 MCP 配置
            mcp_config = self._load_mcp_config()
            
            if not mcp_config:
                return "❌ 没有找到有效的 MCP 配置，请在前端界面配置 MCP 工具后再试。"
            
            print(f"📋 当前 MCP 配置: {list(mcp_config.keys())}")

            client = MultiServerMCPClient(mcp_config)

            tools = await client.get_tools()
            
            # 创建一个ChatOpenAI实例
            llm = ChatOpenAI(model_name=os.getenv("MODEL"), temperature=0)

            # 1. 问题分析 Agent
            analysis_agent = create_react_agent(
                name="analysis_agent",
                model=llm,
                prompt="""
                你是一个问题分析专家，负责将问题进行分解，看看有什么概念是你不知道的，或者需要澄清的，都指出来。
                """,
                tools=[]
            )

            # 2. 计划制定 Agent
            planning_agent = create_react_agent(
                name="planning_agent",
                model=llm,
                prompt="""
                你是一个专门做计划的专家。根据问题的分析结果，制定一个详细的、分步骤的行动计划，说明为了回答这个问题需要做什么，比如查阅哪些资料等。
                """,
                tools=[]
            )
            
            # 3. 计划执行 Agent (新增)
            execution_agent = create_react_agent(
                name="execution_agent",
                model=llm,
                prompt="""
                你是一个计划执行专家。你的任务是严格按照给定的计划，一步一步地使用工具来执行。
                你需要详细记录每一步的执行过程和产出的结果。你有一些工具供你使用。
                """,
                tools=tools
            )

            # 4. 答案整合 Agent (新增)
            integration_agent = create_react_agent(
                name="integration_agent",
                model=llm,
                prompt="""
                你是一个整合专家。根据计划执行的所有结果，进行全面地分析和总结。
                你的目标是形成一个完整、流畅、专业且格式优美的最终答案。
                请直接输出最终答案，不要包含任何多余的思考过程或解释。
                """,
                tools=[]
            )


            # 创建包含四个 agent 的 supervisor 工作流
            forwarding_tool = create_forward_message_tool()
            workflow = create_supervisor(
                [analysis_agent, planning_agent, execution_agent, integration_agent],
                model=llm,
                # 将新工具添加到 supervisor 可用工具列表中
                tools=[forwarding_tool],
                prompt=(
                    "你是一个团队总监 👨‍💼，负责协调一个由四名专家组成的精英团队来回答用户的问题。\n\n"
                    "你的团队成员包括：\n"
                    "1.  **问题分析专家 (analysis_agent)** 🧐: 负责深入分析和分解用户提出的问题。\n"
                    "2.  **计划制定专家 (planning_agent)** 📝: 根据问题分析结果，制定一个详细的、分步骤的行动计划。\n"
                    "3.  **计划执行专家 (execution_agent)** 🛠️: 严格按照计划，使用可用工具执行每一个步骤，并收集结果。\n"
                    "4.  **答案整合专家 (integration_agent)** ✍️: 将所有执行结果整合成一个全面、清晰且连贯的最终答案。\n\n"
                    "**工作流程** 🚀:\n"
                    "1.  你首先将用户的问题发给【问题分析专家】进行拆解。\n"
                    "2.  然后，将分析结果传递给【计划制定专家】来创建行动计划。\n"
                    "3.  接下来，将制定的计划交给【计划执行专家】来付诸行动。\n"
                    "4.  然后，将所有的执行成果交给【答案整合专家】进行最后的整理和润色。\n"
                    "5.  **最后，当【答案整合专家】完成后，你必须调用 `forward_message` 工具，并将 `from_agent` 设置为 `integration_agent`**，以直接将最终答案作为输出。这可以节省成本并保证结果的原汁原味。\n\n"
                    "请严格按照此流程进行，尤其是在最后一步使用 `forward_message` 工具。"
                )
            )

            # 编译并运行工作流
            app = workflow.compile()
            print("🚀 Starting LangGraph Supervisor Workflow...")
            response = await app.ainvoke({
                "messages": [
                    {
                        "role": "user",
                        "content": user_question
                    }
                ]
            })
            print("✅ Workflow finished.")
            print("Final Response:", response)

            # 返回最终由 supervisor 整合过的内容
            return response["messages"][-1].content

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ LangGraph MCP Agent 执行失败！\n\n" \
                   f"**错误信息**: {str(e)}\n\n" \
                   f"请检查您的 MCP 服务配置和网络连接。"
