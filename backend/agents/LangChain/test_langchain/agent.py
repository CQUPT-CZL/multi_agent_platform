# agents/crewai_agents/financial_analyst.py
from agents.base_agent import BaseAgent
import asyncio
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import dotenv

dotenv.load_dotenv()

class LangChainTestAgent(BaseAgent):

    @property
    def framework(self) -> str:
        return "LangChain"

    @property
    def name(self) -> str:
        return "langchain_test_agent"

    @property
    def display_name(self) -> str:
        return "LangChain连通性测试"

    @property
    def description(self) -> str:
        return "测试LangChain框架的基本功能和链式逻辑。"

    async def run(self, message: str, model: str, conversation_id: str) -> str:
        try:
            print("开始LangChain测试...")
            llm = ChatOpenAI(temperature=0, model="deepseek-chat")
            chain = llm | StrOutputParser()
            print(1)
            result = await chain.ainvoke(message)
            print(result)
            
            return f"✅ LangChain测试成功！\n\n" \
                   f"框架: {self.framework}\n" \
                   f"模型: {model}\n" \
                   f"会话ID: {conversation_id}\n\n" \
                   f"结果: {result}"
                   
        except Exception as e:
            return f"❌ LangChain测试失败！\n\n" \
                   f"错误信息: {str(e)}\n" \
                   f"请检查LangChain依赖是否正确安装。"