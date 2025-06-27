import os
import json
from typing import List, Dict, Any, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from agents.base_agent import BaseAgent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# 定义一个常量来限制最大循环次数，防止无限循环
MAX_LOOPS = 7

# 定义图（Graph）的状态，它将贯穿整个工作流
class AgentState(TypedDict):
    # messages 列表用于在不同 Agent 之间传递信息
    messages: Annotated[list, add_messages]
    # 原始问题，方便随时回溯
    original_question: str
    # 问题分析的结果
    analysis: str
    # 制定的计划
    plan: str
    # 将执行历史记录为简单的字符串列表，以控制上下文长度
    execution_history: list[str]
    # [NEW] 增加一个计数器来跟踪循环次数
    loop_count: int


class LangGraphCoTAgent(BaseAgent):
    """
    使用自定义的图（Graph）工作流生成一个包含完整思考过程的 CoT（Chain-of-Thought）长思维链。
    工作流: 分析 -> 计划 -> [执行 <-> 判断] (循环) -> 总结
    """

    @property
    def framework(self) -> str:
        return "LangGraph"

    @property
    def name(self) -> str:
        return "langgraph_cot_agent_custom_flow"

    @property
    def display_name(self) -> str:
        return "CoT 生成 Agent (带约束的自定义循环)"

    @property
    def description(self) -> str:
        return "通过分析、计划、循环执行和总结的自定义工作流，生成包含完整思考过程的 CoT 数据。"

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
        print(f"--- 🏃‍♂️ Running Custom LangGraph Agent for conversation: {conversation_id} ---")
        
        try:
            user_question = message[-1]["content"]

            mcp_config = self._load_mcp_config()
            if not mcp_config:
                return "❌ 没有找到有效的 MCP 配置，请在前端界面配置 MCP 工具后再试。"
            
            print(f"📋 当前 MCP 配置: {list(mcp_config.keys())}")

            client = MultiServerMCPClient(mcp_config)
            tools = await client.get_tools()
            
            llm = ChatOpenAI(model_name=os.getenv("MODEL", model), temperature=0)

            # 1. 问题分析 Agent 🧐
            analysis_agent = create_react_agent(
                model=llm,
                prompt="""
                你是一个问题分析专家 🧐。你的任务是深入剖析用户提出的问题，识别其核心，并清晰地罗列出你的分析结果。请保持回答简洁扼要。
                """,
                tools=[]
            )

            # 2. 计划制定 Agent 📝
            planning_agent = create_react_agent(
                model=llm,
                prompt="""
                你是一个计划制定专家 📝。根据问题分析结果，制定一个清晰、分步骤的行动计划。
                重要提示：整个计划【不要超过5个步骤】，并确保每一步都具体可操作。
                """,
                tools=[]
            )
            
            # 3. 计划执行 Agent 🛠️
            execution_agent = create_react_agent(
                model=llm,
                prompt="""
                你是一个一丝不苟的计划执行者 🛠️。严格按照计划和现有历史，使用工具执行【下一个未完成】的步骤。
                请一次只执行【一个】步骤，并简要报告你的操作和结果。
                """,
                tools=tools
            )

            # 4. 判断 Agent 🤔
            judgement_agent = create_react_agent(
                model=llm,
                prompt="""
                你是一个判断专家 🤔。查看计划和执行历史，判断计划是否已全部完成。
                - 如果已完成，只回答 `finished`。
                - 如果未完成，只回答 `continue`。
                不要添加任何多余的解释。
                """,
                tools=[]
            )

            # 5. 总结 Agent ✍️
            summarization_agent = create_react_agent(
                model=llm,
                prompt="""
                你是一个总结报告专家 ✍️。基于整个工作流程，生成一份全面而详细的最终报告。
                请务必按照以下格式组织你的报告：

                ## 🌟 我的思考与执行全过程 🌟

                ### 1. 🤔 问题分析
                *最初我是这样理解这个问题的...*

                ### 2. � 行动计划
                *为此，我制定了如下的行动计划...*

                ### 3. 🛠️ 执行过程
                *我是这样一步步执行的...（请在这里整合所有执行步骤和结果）*

                ### 4. ✅ 最终答案
                *基于以上所有信息，我的最终结论是...*

                请确保报告内容详实、格式优美、语言流畅专业。直接输出这份报告。
                """,
                tools=[]
            )

            workflow = StateGraph(AgentState)

            async def run_analysis(state: AgentState):
                print("--- 节点: 🧐 问题分析 ---")
                response = await analysis_agent.ainvoke(state)
                return {"analysis": response['messages'][-1].content, "messages": response['messages']}

            async def run_planning(state: AgentState):
                print("--- 节点: 📝 计划制定 ---")
                prompt = f"这是问题分析的结果，请基于此制定计划：\n\n{state['analysis']}"
                response = await planning_agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
                return {"plan": response['messages'][-1].content, "messages": response['messages']}

            async def run_execution(state: AgentState):
                print(f"--- 节点: 🛠️ 计划执行 (循环 #{state.get('loop_count', 0) + 1}) ---")
                history_str = "\n".join(state.get('execution_history', []))
                prompt = f"""
                这是计划和历史，请执行下一步:
                计划: {state['plan']}
                历史: {history_str}
                """
                response = await execution_agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
                
                new_history_entry = response['messages'][-1].content
                new_history = state.get('execution_history', []) + [new_history_entry]
                
                return {
                    "execution_history": new_history, 
                    "messages": response['messages'],
                    "loop_count": state.get('loop_count', 0) + 1 # [MODIFIED] 更新循环计数
                }

            async def run_judgement(state: AgentState):
                print("--- 节点: 🤔 判断 ---")
                history_str = "\n".join(state.get('execution_history', []))
                prompt = f"""
                判断计划是否完成。
                计划: {state['plan']}
                历史: {history_str}
                """
                response = await judgement_agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
                return {"messages": response['messages']}

            async def run_summary(state: AgentState):
                print("--- 节点: ✍️ 总结报告 ---")
                history_str = "\n".join(f"- {step}" for step in state.get('execution_history', []))
                
                termination_reason = ""
                if state.get('loop_count', 0) >= MAX_LOOPS:
                    termination_reason = "**注意：由于达到最大循环次数，任务被提前终止。以下是到目前为止的结果总结。**\n\n"

                prompt = f"""
                {termination_reason}整个任务流程已经结束，请根据以下所有信息，生成最终的详细报告。

                **原始问题**: {state['original_question']}
                **问题分析**: {state['analysis']}
                **行动计划**: {state['plan']}
                **完整执行历史**:
{history_str}
                """
                response = await summarization_agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
                return {"messages": response['messages']}

            workflow.add_node("analysis_agent", run_analysis)
            workflow.add_node("planning_agent", run_planning)
            workflow.add_node("execution_agent", run_execution)
            workflow.add_node("judgement_agent", run_judgement)
            workflow.add_node("summarization_agent", run_summary)
            
            workflow.set_entry_point("analysis_agent")
            workflow.add_edge("analysis_agent", "planning_agent")
            workflow.add_edge("planning_agent", "execution_agent")
            
            # [MODIFIED] 更新判断逻辑以包含最大循环检查
            def should_continue(state: AgentState):
                last_message = state['messages'][-1].content.strip().lower()
                loop_count = state.get('loop_count', 0)
                print(f"--- 判断结果: '{last_message}', 当前循环次数: {loop_count} ---")

                if loop_count >= MAX_LOOPS:
                    print(f"--- 🚫 达到最大循环次数 ({MAX_LOOPS})，强制结束。 ---")
                    return "summarization_agent"
                
                if "finished" in last_message:
                    return "summarization_agent"
                else:
                    return "execution_agent"

            workflow.add_conditional_edges(
                "judgement_agent",
                should_continue,
                {"execution_agent": "execution_agent", "summarization_agent": "summarization_agent"}
            )
            
            workflow.add_edge("execution_agent", "judgement_agent")
            workflow.add_edge("summarization_agent", END)

            app = workflow.compile()
            print("🚀 Starting LangGraph Custom Workflow...")
            
            # [MODIFIED] 初始化状态，包括 loop_count
            initial_state = {
                "messages": [HumanMessage(content=user_question)],
                "original_question": user_question,
                "execution_history": [],
                "loop_count": 0,
            }
            final_state = await app.ainvoke(initial_state)
            
            print("✅ Workflow finished.")
            final_response = final_state['messages'][-1].content
            print("Final Response:", final_response)

            return final_response

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ LangGraph Agent 执行失败！\n\n" \
                   f"**错误信息**: {str(e)}\n\n" \
                   f"请检查您的 MCP 服务配置和网络连接。"
