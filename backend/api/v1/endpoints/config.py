# 文件路径: backend/api/v1/endpoints/config.py

from fastapi import APIRouter
from core.agent_registry import agent_registry # 假设注册中心在这里

# 为这个模块创建一个独立的 router 实例
router = APIRouter()

@router.get("/config")
def get_system_config():
    """
    获取系统所有可用框架和Agent的结构化配置。
    """
    config_data = {}
    for agent_instance in agent_registry.agents.values():
        fw = agent_instance.framework
        if fw not in config_data:
            config_data[fw] = []
        
        config_data[fw].append({
            "name": agent_instance.name,
            "display_name": agent_instance.display_name,
            "description": agent_instance.description,
        })
        
    return config_data