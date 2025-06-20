# agents/base_agent.py
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    
    @property
    @abstractmethod
    def framework(self) -> str:
        """Agent所属的框架名称, e.g., 'crewAI'"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent的唯一技术名称 (用于API调用), e.g., 'crewai_financial_analyst'"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Agent在UI中显示的友好名称, e.g., '金融市场分析'"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Agent的简短描述，可用作帮助提示。"""
        pass

    @abstractmethod
    async def run(self, message: str, model: str, conversation_id: str) -> str:
        """执行Agent任务的异步方法。"""
        pass