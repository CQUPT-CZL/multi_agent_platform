# 请确保已安装必要的依赖包:
# pip install langchain langchain-openai langchain-community google-search-results python-dotenv

from agents.base_agent import BaseAgent
from typing import List, Dict, Any
import os
import dotenv

# LangChain 核心组件
from langchain_openai import ChatOpenAI
# 【新】导入 create_react_agent 和 ReAct 相关的 prompt 工具
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate # ReAct 通常使用这个
from langchain import hub # 从 LangChain Hub 加载成熟的 ReAct prompt

from langchain_core.messages import AIMessage, HumanMessage

# 我们将要使用的工具是 Google Serper
from langchain_community.tools.google_serper import GoogleSerperRun
from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper

# 加载 .env 文件中的环境变量 (例如 OPENAI_API_KEY, SERPER_API_KEY)
dotenv.load_dotenv()

# 启动时检查 SERPER_API_KEY 是否存在
if not os.getenv("SERPER_API_KEY"):
    print("⚠️ 警告: 环境变量 SERPER_API_KEY 未设置。搜索工具将无法工作。")
    print("   请访问 https://serper.dev/ 获取免费API密钥。")


class LangChainSearchAgent(BaseAgent):
    """
    一个集成了Google Serper搜索工具的LangChain Agent，
    【新】采用 ReAct 模式进行思考和决策。
    """

    @property
    def framework(self) -> str:
        return "LangChain"

    @property
    def name(self) -> str:
        # 这是API调用的唯一标识符
        return "langchain_search_agent_react" # 建议改个名字以作区分

    @property
    def display_name(self) -> str:
        # 这是在前端UI上显示的友好名称
        return "Web搜索Agent (ReAct)"

    @property
    def description(self) -> str:
        return "使用ReAct模式和Google Serper搜索引擎来回答问题。"

    async def run(self, message: List[Dict[str, Any]], model: str, conversation_id: str) -> str:
        """
        异步运行Agent，处理带有历史记录的对话。
        """
        print(f"--- Running LangChainSearchAgent (ReAct) for conversation: {conversation_id} ---")
        try:
            # 1. 初始化大语言模型 (LLM)
            llm = ChatOpenAI(temperature=0, model="deepseek-chat")

            # 2. 定义可用的工具列表
            # 【修正】需要先创建API Wrapper，再将其传入工具
            search_wrapper = GoogleSerperAPIWrapper()
            tools = [GoogleSerperRun(api_wrapper=search_wrapper)]

            # 3. 【核心改动】创建 ReAct 模式的 Prompt
            # ReAct 的 prompt 结构很特别，它需要明确定义工具、思考过程和最终答案的格式。
            # 为了方便，我们直接从 LangChain Hub 加载一个已经优化好的 ReAct prompt。
            prompt_template = hub.pull("hwchase17/react-chat")

            # 4. 【核心改动】创建 Agent
            # 使用 create_react_agent 来将 LLM、工具和 ReAct prompt 绑定在一起
            agent = create_react_agent(llm, tools, prompt_template)

            # 5. 创建Agent执行器 (AgentExecutor) (这部分不变)
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

            # 6. 准备输入数据
            user_input = message[-1]["content"]
            
            chat_history_messages = []
            for message in message[:-1]:
                if message["role"] == "user":
                    chat_history_messages.append(HumanMessage(content=message["content"]))
                elif message["role"] == "assistant":
                    chat_history_messages.append(AIMessage(content=message["content"]))
            
            # 7. 异步调用Agent执行器
            # ReAct模式的输入变量通常是 'input' 和 'chat_history'
            result = await agent_executor.ainvoke({
                "input": user_input,
                "chat_history": chat_history_messages
            })

            return result.get("output", "抱歉，我无法处理您的请求。")

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Agent 执行失败！\n\n" \
                   f"**错误信息**: {str(e)}\n\n" \
                   f"请检查您的API密钥（OPENAI_API_KEY, SERPER_API_KEY）和依赖项是否都已正确设置。"
