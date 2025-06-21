# 请确保已安装必要的依赖包:
# pip install crewai crewai-tools langchain-openai python-dotenv

from agents.base_agent import BaseAgent
from typing import List, Dict, Any
import os
import dotenv

# CrewAI 核心组件
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from langchain_openai import ChatOpenAI

# 加载环境变量
dotenv.load_dotenv()

# 检查必要的API密钥
if not os.getenv("SERPER_API_KEY"):
    print("⚠️ 警告: 环境变量 SERPER_API_KEY 未设置。搜索工具将无法工作。")
    print("   请访问 https://serper.dev/ 获取免费API密钥。")

if not os.getenv("OPENAI_API_KEY"):
    print("⚠️ 警告: 环境变量 OPENAI_API_KEY 未设置。")


class CrewAIResearchAgent(BaseAgent):
    """
    一个使用CrewAI框架的研究Agent，包含三个专门的任务：
    1. 文章搜集 - 根据用户问题搜索相关文章和资料
    2. 内容审核 - 对搜集到的内容进行质量评估和筛选
    3. 内容总结 - 将审核后的内容整理成结构化的总结报告
    """

    @property
    def framework(self) -> str:
        return "CrewAI"

    @property
    def name(self) -> str:
        return "crewai_research_agent"

    @property
    def display_name(self) -> str:
        return "研究分析团队 (CrewAI)"

    @property
    def description(self) -> str:
        return "使用CrewAI框架的多Agent协作团队，专门进行文章搜集、内容审核和总结分析。"

    def _create_agents(self, llm):
        """
        创建三个专门的Agent
        """
        # 搜索工具
        search_tool = SerperDevTool()
        
        # 1. 文章搜集专家
        researcher = Agent(
            role='资料搜集专家',
            goal='根据用户的问题，搜集相关的文章、资料和信息',
            backstory="""你是一位经验丰富的资料搜集专家，擅长使用各种搜索工具
            找到与用户问题相关的高质量文章和资料。你能够识别权威来源，
            并确保搜集到的信息具有时效性和相关性。""",
            verbose=True,
            allow_delegation=False,
            tools=[search_tool],
            llm=llm
        )

        # 2. 内容审核专家
        reviewer = Agent(
            role='内容审核专家',
            goal='对搜集到的文章和资料进行质量评估、事实核查和可信度分析',
            backstory="""你是一位严谨的内容审核专家，具有敏锐的批判性思维。
            你能够评估信息来源的可信度，识别潜在的偏见或错误信息，
            并对内容的质量和相关性进行专业判断。""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

        # 3. 内容总结专家
        summarizer = Agent(
            role='内容总结专家',
            goal='将审核后的内容整理成结构化、易懂的总结报告',
            backstory="""你是一位优秀的内容总结专家，擅长将复杂的信息
            整理成清晰、结构化的报告。你能够提取关键要点，
            组织逻辑结构，并以用户友好的方式呈现信息。""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

        return researcher, reviewer, summarizer

    def _create_tasks(self, user_question: str, researcher, reviewer, summarizer):
        """
        创建三个相互关联的任务
        """
        # 任务1: 文章搜集
        research_task = Task(
            description=f"""
            根据用户的问题："{user_question}"
            
            请执行以下搜集任务：
            1. 使用搜索工具查找相关的文章、新闻、研究报告等资料
            2. 搜集至少3-5个不同来源的相关内容
            3. 记录每个来源的标题、链接、发布时间和主要内容摘要
            4. 确保搜集的内容与用户问题高度相关
            
            输出格式：
            - 来源1：[标题] - [链接] - [时间] - [内容摘要]
            - 来源2：[标题] - [链接] - [时间] - [内容摘要]
            - ...
            """,
            agent=researcher,
            expected_output="包含多个相关资料来源的详细列表，每个来源都有完整的元信息和内容摘要"
        )

        # 任务2: 内容审核
        review_task = Task(
            description=f"""
            对搜集到的资料进行全面审核，针对用户问题："{user_question}"
            
            请执行以下审核任务：
            1. 评估每个来源的可信度和权威性
            2. 检查信息的时效性和准确性
            3. 识别可能的偏见或不准确信息
            4. 筛选出最相关和最可靠的内容
            5. 对每个来源给出质量评分（1-10分）
            
            审核标准：
            - 来源权威性（官方机构、知名媒体、专业期刊等）
            - 内容相关性（与用户问题的匹配度）
            - 信息时效性（发布时间的新近程度）
            - 内容完整性（信息是否完整、逻辑清晰）
            """,
            agent=reviewer,
            expected_output="经过质量评估的资料清单，包含每个来源的可信度分析和质量评分",
            context=[research_task]
        )

        # 任务3: 内容总结
        summary_task = Task(
            description=f"""
            基于审核后的高质量资料，为用户问题："{user_question}" 创建综合总结报告
            
            请执行以下总结任务：
            1. 整合所有审核通过的信息
            2. 提取关键要点和核心观点
            3. 组织成逻辑清晰的结构
            4. 提供平衡、客观的分析
            5. 包含具体的数据和事实支撑
            
            报告结构：
            ## 问题概述
            [对用户问题的理解和背景介绍]
            
            ## 主要发现
            [基于搜集资料的核心发现，分点列出]
            
            ## 详细分析
            [深入分析各个方面，引用具体来源]
            
            ## 结论与建议
            [基于分析得出的结论和实用建议]
            
            ## 参考来源
            [列出所有引用的高质量来源]
            """,
            agent=summarizer,
            expected_output="结构化的综合研究报告，包含问题分析、主要发现、详细论述和实用建议",
            context=[research_task, review_task]
        )

        return research_task, review_task, summary_task

    async def run(self, message: List[Dict[str, Any]], model: str, conversation_id: str) -> str:
        """
        异步运行CrewAI研究团队
        """
        print(f"--- Running CrewAI Research Agent for conversation: {conversation_id} ---")
        
        try:
            # 获取用户的最新问题
            user_question = message[-1]["content"]
            
            # 初始化LLM
            llm = ChatOpenAI(
                model="deepseek-chat",
                temperature=0.1
            )
            
            # 创建三个专门的Agent
            researcher, reviewer, summarizer = self._create_agents(llm)
            
            # 创建三个相关联的任务
            research_task, review_task, summary_task = self._create_tasks(
                user_question, researcher, reviewer, summarizer
            )
            
            # 创建Crew团队
            crew = Crew(
                agents=[researcher, reviewer, summarizer],
                tasks=[research_task, review_task, summary_task],
                process=Process.sequential,  # 按顺序执行任务
                verbose=True
            )
            
            # 执行任务
            print("🚀 启动CrewAI研究团队...")
            result = crew.kickoff()
            
            return f"""# CrewAI 研究团队分析报告

**用户问题**: {user_question}

---

{result}

---

*本报告由CrewAI多Agent协作团队生成，包含文章搜集、内容审核和总结分析三个专业环节。*
            """
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ CrewAI研究团队执行失败！\n\n" \
                   f"**错误信息**: {str(e)}\n\n" \
                   f"请检查您的API密钥（OPENAI_API_KEY, SERPER_API_KEY）和CrewAI依赖项是否都已正确安装和配置。\n\n" \
                   f"安装命令: `pip install crewai crewai-tools`"