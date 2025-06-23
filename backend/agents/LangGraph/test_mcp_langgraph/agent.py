import os
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

class LangGraphMCPAgent(BaseAgent):
    """
    一个使用 LangGraph 和 Multi-Server MCP Client 的 Agent，
    能够与通过 MCP 协议暴露的多个工具服务进行交互。
    """

    @property
    def framework(self) -> str:
        return "LangGraph"

    @property
    def name(self) -> str:
        return "langgraph_mcp_agent"

    @property
    def display_name(self) -> str:
        return "多工具协作Agent (LangGraph)"

    @property
    def description(self) -> str:
        return "使用 LangGraph 和 MCP Client 与数学和天气等多个工具进行交互。"

    async def run(self, message: List[Dict[str, Any]], model: str, conversation_id: str) -> str:
        """
        执行 LangGraph Agent 的任务。
        """
        print(f"--- Running LangGraph MCP Agent for conversation: {conversation_id} ---")
        
        try:
            user_question = message[-1]["content"]

            # 获取当前项目根目录
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            # math_server_path = os.path.join(project_root, "mcp_server", "math_server.py")

            client = MultiServerMCPClient(
                {
                    # "math": {
                    #     "command": "python",
                    #     "args": [math_server_path],
                    #     "transport": "stdio",
                    # },
                    "weather": {
                        # 确保 weather_server 在 8000 端口上运行
                        "url": "http://localhost:8005/mcp/",
                        "transport": "streamable_http",
                    }
                }
            )

            tools = await client.get_tools()
            print(tools)
            # 创建一个ChatOpenAI实例
            
            llm = ChatOpenAI(model_name=os.getenv("MODEL"), temperature=0)
            agent_executor = create_react_agent(llm, tools)
            
            print(f"Invoking LangGraph agent with question: {user_question}")
            response = await agent_executor.ainvoke({"messages": [("human", user_question)]})
            

            return response['messages'][-1].content

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ LangGraph MCP Agent 执行失败！\n\n" \
                   f"**错误信息**: {str(e)}\n\n" \
                   f"请确保所有依赖项已正确安装，并且 mcp_server/math_server.py 路径正确。"