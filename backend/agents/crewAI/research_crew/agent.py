# 请确保已安装必要的依赖包:
# pip install crewai crewai-tools langchain-openai python-dotenv

import os
import dotenv
from typing import List, Dict, Any

# CrewAI 核心组件
from crewai import Agent, Task, Crew, Process
# 注意：这里我们使用Langchain_openai，如果想用LiteLLM包装deepseek-chat，需要修改为LiteLLM
from langchain_openai import ChatOpenAI
# from litellm import completion as LiteLLMCompletion # 如果使用LiteLLM

# 从你的项目结构中导入 BaseAgent
# 假设 BaseAgent 是一个抽象基类或者包含一些通用属性和方法的类
from agents.base_agent import BaseAgent 

# 加载环境变量
dotenv.load_dotenv()

# 检查 OPENAI_API_KEY 是否设置
if not os.getenv("OPENAI_API_KEY"):
    print("⚠️ 警告: 环境变量 OPENAI_API_KEY 未设置。请确保在 .env 文件中配置了 'OPENAI_API_KEY'。")

# 如果你想使用 LiteLLM 封装 DeepSeek，需要设置 DEEPSEEK_API_KEY
# if not os.getenv("DEEPSEEK_API_KEY"):
#     print("⚠️ 警告: 环境变量 DEEPSEEK_API_KEY 未设置。")


class CrewAIResearchAgent(BaseAgent):
    """
    一个简化的CrewAI研究Agent示例，只包含一个Agent和一个Task。
    用于演示CrewAI的基础用法。
    """

    @property
    def framework(self) -> str:
        return "CrewAI"

    @property
    def name(self) -> str:
        return "crewai_single_research_agent"

    @property
    def display_name(self) -> str:
        return "单Agent研究助手 (CrewAI 简化版)"

    @property
    def description(self) -> str:
        return "一个使用CrewAI框架的简化版Agent，专注于单一研究任务。"

    def _create_agents(self, llm):
        """
        创建单个研究员Agent。
        """
        # 1. 创建一个“研究员”Agent
        researcher_agent = Agent(
            role='AI研究员',
            goal='深入研究并总结人工智能的最新趋势',
            backstory="""你是一位经验丰富的AI研究员，
                         擅长从各种来源获取信息，并能清晰地总结复杂的技术概念。
                         你的目标是为你的团队提供最新、最准确的AI发展报告。""",
            verbose=True,  # 设置为True可以看到Agent的思考过程
            allow_delegation=False,  # 简化起见，不允许Agent将任务委托出去
            tools=[],  # 在这个简化版中，我们不添加工具。如果需要联网搜索，这里可以添加 CrewAI Tools。
            llm=llm
        )
        return researcher_agent # 返回单个 Agent

    def _create_tasks(self, user_question: str, researcher_agent):
        """
        创建单个研究任务，分配给研究员Agent。
        """
        # 给研究员Agent分配一个任务
        research_summary_task = Task(
            description=f"""
            根据用户的问题："{user_question}"，
            
            请全面分析最新的行业报告和研究，总结出至少三个当前最热门的相关发展趋势。
            你的总结应该简洁明了，突出关键技术和应用场景。
            
            具体要求：
            1. 识别并列出至少三个最重要的趋势。
            2. 对每个趋势进行简要描述，包括其核心概念和潜在影响。
            3. 确保信息最新，参考2025年6月及以后的数据（如果可用）。
            """,
            expected_output="""一份结构化的报告，包含：
                             - 标题：[关于{user_question}的最新趋势总结]
                             - 趋势1：名称和简要描述
                             - 趋势2：名称和简要描述
                             - 趋势3：名称和简要描述
                             - 总结：对未来发展的简短展望。""",
            agent=researcher_agent  # 这个任务分配给 'researcher_agent'
        )
        return research_summary_task # 返回单个 Task

    async def run(self, message: List[Dict[str, Any]], model: str, conversation_id: str) -> str:
        """
        异步运行简化的CrewAI研究Agent。
        """
        print(f"--- 运行简化的CrewAI研究Agent (会话ID: {conversation_id}) ---")

        try:
            # 获取用户的最新问题
            user_question = message[-1]["content"]

            # 初始化LLM
            # 注意：这里默认使用 Langchain_OpenAI。
            # 如果你想用 LiteLLM 包装 DeepSeek，你需要像下面这样修改：
            # llm = LiteLLMCompletion(model="deepseek/deepseek-chat", api_key=os.getenv("DEEPSEEK_API_KEY"), temperature=0.1)
            llm = ChatOpenAI(
                model="deepseek/deepseek-chat",
                temperature=0.1
            )
            print(f"使用的LLM模型: {llm.model_name} (或 DeepSeek via LiteLLM)")

            # 创建单个研究员Agent
            researcher_agent = self._create_agents(llm)

            # 创建单个研究任务
            research_summary_task = self._create_tasks(user_question, researcher_agent)

            # 创建Crew团队
            my_crew = Crew(
                agents=[researcher_agent],  # 团队里只有一个研究员Agent
                tasks=[research_summary_task],  # 团队的任务就是这个研究任务
                verbose=True,  # 设置为2可以看到更详细的执行过程
                process=Process.sequential  # 任务会按顺序执行 (这里只有一个，所以无所谓顺序)
            )

            # 执行任务
            print("🚀 启动CrewAI单Agent研究任务...")
            result = my_crew.kickoff()

            return f"""# CrewAI 简化版研究报告

**用户问题**: {user_question}

---

{result}

---

*本报告由CrewAI单Agent研究助手生成，专注于核心研究与总结任务。*
            """

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ 简化的CrewAI研究Agent执行失败！\n\n" \
                   f"**错误信息**: {str(e)}\n\n" \
                   f"请检查您的API密钥（OPENAI_API_KEY 或 DEEPSEEK_API_KEY）和CrewAI依赖项是否都已正确安装和配置。\n\n" \
                   f"安装命令: `pip install crewai crewai-tools langchain-openai python-dotenv`"