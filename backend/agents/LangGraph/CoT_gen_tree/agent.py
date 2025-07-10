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

# 定义图（Graph）的状态，它将贯穿整个工作流
class AgentState(TypedDict):
    # messages 列表用于在不同 Agent 之间传递信息
    messages: Annotated[list, add_messages]
    # 原始问题，方便随时回溯
    original_question: str
    # 纯大模型回答结果
    llm_response: str
    # 搜索工具回答结果
    search_response: str
    # RAG工具回答结果（如果有）
    rag_response: str
    # 可用的工具列表
    available_tools: list
    # 是否有RAG工具
    has_rag_tool: bool


class LangGraphCoTTreeAgent(BaseAgent):
    """
    使用树状并行工作流的 CoT（Chain-of-Thought）Agent。
    工作流: 用户请求 -> [纯LLM回答 | 搜索工具回答 | RAG工具回答] (并行) -> 总结汇总
    """

    @property
    def framework(self) -> str:
        return "LangGraph"

    @property
    def name(self) -> str:
        return "langgraph_cot_tree_agent"

    @property
    def display_name(self) -> str:
        return "CoT 生成 Agent (树状并行执行)"

    @property
    def description(self) -> str:
        return "通过多路并行执行（纯LLM、搜索工具、RAG工具）的树状工作流，生成包含完整思考过程的 CoT 数据。"

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

    def _categorize_tools(self, tools: list) -> Dict[str, list]:
        """
        将工具按类型分类
        """
        search_tools = []
        rag_tools = []
        other_tools = []
        
        for tool in tools:
            tool_name = tool.name.lower() if hasattr(tool, 'name') else str(tool).lower()
            print(tool_name)
            # tool_desc = tool.description.lower() if hasattr(tool, 'description') else str(tool).lower()
            
        
            # 识别搜索工具
            if any(keyword in tool_name for keyword in ['get', 'search', 'web', 'google', 'bing', '搜索']):
                search_tools.append(tool)
            # 识别RAG工具
            elif any(keyword in tool_name for keyword in ['rag', 'retrieval', 'knowledge', 'document', 'vector', '检索', '知识库']):
                rag_tools.append(tool)
            else:
                other_tools.append(tool)
        
        return {
            'search': search_tools,
            'rag': rag_tools,
            'other': other_tools
        }

    async def run(self, message: List[Dict[str, Any]], model: str, conversation_id: str) -> str:
        """
        执行 LangGraph Tree Agent 的任务。
        """
        print(f"--- 🌳 Running LangGraph Tree Agent for conversation: {conversation_id} ---")
        
        try:
            user_question = message[-1]["content"]

            mcp_config = self._load_mcp_config()
            if not mcp_config:
                return "❌ 没有找到有效的 MCP 配置，请在前端界面配置 MCP 工具后再试。"
            
            print(f"📋 当前 MCP 配置: {list(mcp_config.keys())}")

            client = MultiServerMCPClient(mcp_config)
            tools = await client.get_tools()
            
            # 分类工具
            categorized_tools = self._categorize_tools(tools)
            print(f"🔧 工具分类结果: 搜索工具 {len(categorized_tools['search'])} 个, RAG工具 {len(categorized_tools['rag'])} 个, 其他工具 {len(categorized_tools['other'])} 个")
            
            llm = ChatOpenAI(model_name=os.getenv("MODEL", model), temperature=0)

            # 1. 纯大模型回答 Agent 🤖
            pure_llm_agent = create_react_agent(
                model=llm,
                prompt="""
                你是一个知识渊博的AI助手 🤖。请仅基于你的内置知识来回答用户的问题。
                不要使用任何外部工具，只依靠你的训练数据和推理能力。
                请提供详细、准确且有帮助的回答。
                """,
                tools=[]  # 不提供任何工具
            )

            # 2. 搜索工具回答 Agent 🔍
            search_agent = create_react_agent(
                model=llm,
                prompt="""
                你是一个搜索专家 🔍。请使用搜索工具来查找最新、最准确的信息来回答用户的问题。
                优先使用搜索工具获取实时信息，然后基于搜索结果提供全面的回答。
                """,
                tools=categorized_tools['search'] + categorized_tools['other']  # 提供搜索工具和其他工具
            )
            
            # 3. RAG工具回答 Agent 📚 (如果有RAG工具)
            rag_agent = None
            if categorized_tools['rag']:
                rag_agent = create_react_agent(
                    model=llm,
                    prompt="""
                    你是一个知识检索专家 📚。请使用RAG（检索增强生成）工具来查找相关文档和知识库信息来回答用户的问题。
                    优先使用检索工具获取相关文档，然后基于检索到的信息提供准确的回答。
                    """,
                    tools=categorized_tools['rag'] + categorized_tools['other']  # 提供RAG工具和其他工具
                )

            # 4. 总结汇总 Agent ✍️
            summary_agent = create_react_agent(
                model=llm,
                prompt="""
                你是一个总结汇总专家 ✍️。你将收到来自不同来源的回答：
                1. 纯大模型回答（基于内置知识）
                2. 搜索工具回答（基于实时搜索）
                3. RAG工具回答（基于知识库检索，如果有的话）
                
                请综合这些信息，生成一份全面、准确且结构化的最终回答。
                
                请按照以下格式组织你的回答：
                
                ## 🌟 综合分析与最终答案 🌟
                
                ### 📊 信息来源分析
                *简要说明各个来源提供的信息特点和价值*
                
                ### ✅ 最终答案
                *基于所有信息源的综合分析，提供最准确、最全面的答案*
                
                ### 🔍 补充说明
                *如有必要，提供额外的背景信息或注意事项*
                
                请确保回答内容详实、逻辑清晰、语言流畅专业。
                """,
                tools=[]
            )

            workflow = StateGraph(AgentState)

            async def run_pure_llm(state: AgentState):
                print("--- 节点: 🤖 纯大模型回答 ---")
                try:
                    response = await pure_llm_agent.ainvoke({"messages": [HumanMessage(content=state['original_question'])]})
                    llm_response = response['messages'][-1].content
                    print(f"🤖 纯大模型回答完成: {len(llm_response)} 字符")
                    return {"llm_response": llm_response, "messages": response['messages']}
                except Exception as e:
                    print(f"❌ 纯大模型回答失败: {e}")
                    return {"llm_response": f"纯大模型回答失败: {str(e)}", "messages": state['messages']}

            async def run_search_tools(state: AgentState):
                print("--- 节点: 🔍 搜索工具回答 ---")
                try:
                    if not categorized_tools['search']:
                        search_response = "没有可用的搜索工具"
                    else:
                        response = await search_agent.ainvoke({"messages": [HumanMessage(content=state['original_question'])]})
                        search_response = response['messages'][-1].content
                    print(f"🔍 搜索工具回答完成: {len(search_response)} 字符")
                    return {"search_response": search_response, "messages": state['messages']}
                except Exception as e:
                    print(f"❌ 搜索工具回答失败: {e}")
                    return {"search_response": f"搜索工具回答失败: {str(e)}", "messages": state['messages']}

            async def run_rag_tools(state: AgentState):
                print("--- 节点: 📚 RAG工具回答 ---")
                try:
                    if not categorized_tools['rag']:
                        rag_response = "没有可用的RAG工具"
                    else:
                        response = await rag_agent.ainvoke({"messages": [HumanMessage(content=state['original_question'])]})
                        rag_response = response['messages'][-1].content
                    print(f"📚 RAG工具回答完成: {len(rag_response)} 字符")
                    return {"rag_response": rag_response, "messages": state['messages']}
                except Exception as e:
                    print(f"❌ RAG工具回答失败: {e}")
                    return {"rag_response": f"RAG工具回答失败: {str(e)}", "messages": state['messages']}

            async def run_summary(state: AgentState):
                print("--- 节点: ✍️ 总结汇总 ---")
                
                # 构建总结提示
                summary_prompt = f"""
                原始问题: {state['original_question']}
                
                以下是来自不同来源的回答，请进行综合分析：
                
                **🤖 纯大模型回答:**
                {state.get('llm_response', '无')}
                
                **🔍 搜索工具回答:**
                {state.get('search_response', '无')}
                
                **📚 RAG工具回答:**
                {state.get('rag_response', '无')}
                
                请基于以上所有信息，生成最终的综合回答。
                """
                
                try:
                    response = await summary_agent.ainvoke({"messages": [HumanMessage(content=summary_prompt)]})
                    print("✅ 总结汇总完成")
                    return {"messages": response['messages']}
                except Exception as e:
                    print(f"❌ 总结汇总失败: {e}")
                    # 如果总结失败，返回一个简单的汇总
                    fallback_summary = f"""
                    ## 🌟 综合分析与最终答案 🌟
                    
                    ### ❌ 总结过程出现错误
                    总结Agent执行失败: {str(e)}
                    
                    ### 📊 各来源回答
                    
                    **🤖 纯大模型回答:**
                    {state.get('llm_response', '无')}
                    
                    **🔍 搜索工具回答:**
                    {state.get('search_response', '无')}
                    
                    **📚 RAG工具回答:**
                    {state.get('rag_response', '无')}
                    """
                    return {"messages": [HumanMessage(content=fallback_summary)]}

            # 添加节点
            workflow.add_node("pure_llm_agent", run_pure_llm)
            workflow.add_node("search_agent", run_search_tools)
            workflow.add_node("rag_agent", run_rag_tools)
            workflow.add_node("summary_agent", run_summary)
            
            # 设置并行执行的工作流程
            workflow.set_entry_point("pure_llm_agent")
            workflow.set_entry_point("search_agent")
            workflow.set_entry_point("rag_agent")
            
            # 所有并行节点都连接到总结节点
            workflow.add_edge("pure_llm_agent", "summary_agent")
            workflow.add_edge("search_agent", "summary_agent")
            workflow.add_edge("rag_agent", "summary_agent")
            workflow.add_edge("summary_agent", END)

            app = workflow.compile()
            print("🚀 Starting LangGraph Tree Workflow...")
            
            # 初始化状态
            initial_state = {
                "messages": [HumanMessage(content=user_question)],
                "original_question": user_question,
                "llm_response": "",
                "search_response": "",
                "rag_response": "",
                "available_tools": tools,
                "has_rag_tool": len(categorized_tools['rag']) > 0
            }
            
            final_state = await app.ainvoke(initial_state, debug=False)
            
            print("✅ Tree Workflow finished.")
            final_response = final_state['messages'][-1].content
            print("Final Response:", final_response)

            return final_response

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ LangGraph Tree Agent 执行失败！\n\n" \
                   f"**错误信息**: {str(e)}\n\n" \
                   f"请检查您的 MCP 服务配置和网络连接。"