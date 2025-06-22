# api/v1/endpoints/chat.py
import agentops
import os

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from core.agent_registry import agent_registry # 导入我们的注册中心

router = APIRouter()

class ChatRequest(BaseModel):
    message: List[dict]  # 消息列表，包含对话历史记录
    agent_name: str
    model: str # 从前端获取模型信息
    conversation_id: str

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):

    agent = agent_registry.get_agent(request.agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{request.agent_name}' not found.")
    
    try:
        # 初始化AgentOps
        agentops.init(
            api_key=os.getenv("AGENTOPS_API_KEY"),
            default_tags=[request.agent_name]
        )
        print(f"开始执行Agent: {request.agent_name}...")
        # 调用统一的run接口，传入所需参数
        response_content = await agent.run(
            message=request.message,
            model=request.model,
            conversation_id=request.conversation_id
        )
        agentops.end_trace()
        return ChatResponse(response=response_content)
    except Exception as e:
        # 统一的错误处理
        raise HTTPException(status_code=500, detail=f"Error executing agent: {str(e)}")