import os
import json
from typing import List, Dict, Any
# [MODIFIED] 不再需要复杂的 State 和图结构，导入简化
from langchain_core.messages import HumanMessage

from agents.base_agent import BaseAgent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# [REFACTORED] Agent 类被大幅简化
class LangGraphReactAgent(BaseAgent):
    """
    一个强大的、自主决策的 ReAct Agent。
    它能根据内部思考，自由决定是否、以及如何使用 `search` 和 `rag_search` 工具，也可能多次使用或不使用。
    """

    @property
    def framework(self) -> str:
        return "LangGraph"

    @property
    def name(self) -> str:
        return "autonomous_react_agent"

    @property
    def display_name(self) -> str:
        return "自主决策 Agent (ReAct 模式)"

    @property
    def description(self) -> str:
        return "一个能自主思考并决定如何使用 Search/RAG 工具的强大代理。"

    def _load_mcp_config(self) -> Dict[str, Any]:
        """
        从 config.json 文件加载 MCP 配置
        """
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

    # [REFACTORED] run 方法被大幅简化
    async def run(self, message: List[Dict[str, Any]], model: str, conversation_id: str) -> str:
        """
        执行自主决策的 ReAct Agent。
        """
        print(f"--- 🏃‍♂️ Running Autonomous ReAct Agent for conversation: {conversation_id} ---")
        
        try:
            user_question = message[-1]["content"]

            # 1. 加载工具箱
            mcp_config = self._load_mcp_config()
            if not mcp_config:
                return "❌ 没有找到有效的 MCP 配置，请在前端界面配置 MCP 工具后再试。"
            
            print(f"📋 当前 MCP 配置: {list(mcp_config.keys())}")
            client = MultiServerMCPClient(mcp_config)
            all_tools = await client.get_tools()
            
            # 🔧 工具过滤：定义你想要使用的工具列表
            # 你可以在这里添加或移除工具名称来控制 Agent 可以使用哪些工具
            allowed_tools = ["retrieve_and_rerank", "get_result"]  # 只允许这些工具
            # 如果你想排除特定工具，可以使用这种方式：
            # excluded_tools = ["unwanted_tool1", "unwanted_tool2"]
            # tools = [tool for tool in all_tools if tool.name not in excluded_tools]
            
            # 过滤工具：只保留允许的工具
            tools = [tool for tool in all_tools if tool.name in allowed_tools]
            
            print(f"🛠️ 所有可用工具: {[tool.name for tool in all_tools]}")
            print(f"✅ 过滤后的工具: {[tool.name for tool in tools]}")
            
            if not tools:
                return "⚠️ 没有可用的工具！请检查工具过滤配置或 MCP 服务状态。"
            
            # 2. 初始化 LLM
            llm = ChatOpenAI(model_name=os.getenv("MODEL", model), temperature=0)

            # [CRITICAL] 3. 定义赋予 Agent 自主决策能力的“大脑” -> 系统提示 (System Prompt)
            # 这是整个 Agent 的灵魂所在
            MASTER_PROMPT = """
            你是一个顶级的问题解决专家和研究员，能力强大且行事严谨。

            **你的工作流程是**:
            1.  **思考**: 在每一步，你都必须先进行思考（Thought）。分析当前情况，判断你是否已经掌握了足够的信息来回答最终问题。
            2.  **行动**: 如果你需要更多信息，就选择一个最合适的工具（Action）来获取。如果你认为信息已经足够，你的行动就是直接输出最终答案。

            **关键词提取规则**:
            当你决定使用工具时，你必须从用户问题中提取关键词，而不是传入完整的问题。
            - 提取1-3个最核心的关键词或短语
            - 关键词应该是名词、专业术语或核心概念
            - 多个关键词用空格分隔
            - 例如："生铁生产过程中的渗碳反应" -> "生铁 渗碳反应"
            - 例如："机器学习算法的优化方法" -> "机器学习 算法优化"

            **你的决策逻辑**:
            - **我是否需要工具?** 如果问题很简单，或者基于历史信息你已经知道了答案，就不要使用任何工具，直接思考并给出最终答案。
            - **该用哪个工具?** 根据问题的性质和可用工具的功能描述，选择最合适的工具来获取信息。
            - **如何提取关键词?** 仔细分析问题，提取最核心的1-3个关键词或短语作为工具的输入参数。
            - **我需要多次使用工具吗?** 完全可以！你可能需要使用不同的关键词来获取不同类型的信息，或者多次使用同一工具来深入挖掘。
            - **什么时候停止?** 当你通过思考（Thought）判断，你从工具中获得的观察（Observation）已经足够全面，能够完美回答用户的原始问题时，你就应该停止使用工具，并提供你的最终答案（Final Answer）。

            **重要**: 
            1. 调用检索工具时，参数必须是关键词，不是完整问题。
            2.调用实时信息搜索问题时，不要关键词，就是完整的问题

            现在，开始解决问题吧！
            """

            # 4. 使用 LangGraph 的预构建功能创建 ReAct Agent 执行器
            # 这会处理所有的“思考->行动->观察”循环，我们不再需要手动构建图
            agent_executor = create_react_agent(model=llm, tools=tools, prompt=MASTER_PROMPT, debug=True)

            print("🚀 Starting Autonomous ReAct Workflow...")
            
            # 5. 执行 Agent 并获取最终结果
            # 使用非流式输出，直接获取完整的响应结果

            
            recursion_limit = 10
            config = {"recursion_limit": recursion_limit}

            result = await agent_executor.ainvoke(
                {"messages": [HumanMessage(content=user_question)]},
                config=config
            )
            
            # 获取最终响应
            final_response = result["messages"][-1].content
            
            print("✅ Workflow finished.")
            print("Final Response:", final_response)

            return final_response

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ LangGraph Agent 执行失败！\n\n" \
                   f"**错误信息**: {str(e)}\n\n" \
                   f"请检查您的 MCP 服务配置和网络连接。"