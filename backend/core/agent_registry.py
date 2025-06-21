# core/agent_registry.py
import importlib
import pkgutil
from typing import Dict
from agents.base_agent import BaseAgent

class AgentRegistry:
    """
    Agent注册中心。
    自动发现并加载所有在 'agents' 包中定义的Agent实例。
    """
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        print("🚀 Initializing Agent Registry...")
        self._discover_agents()
        print(f"✅ Registry initialized. Found {len(self.agents)} agents.")

    def _discover_agents(self):
        """
        自动发现并注册所有在agents子目录中定义的Agent。
        这个方法会自动扫描所有子文件夹，非常灵活。
        """
        import agents # 导入顶层agents包

        # 使用pkgutil.walk_packages来递归遍历agents包下的所有模块
        # 这会自动处理所有的子文件夹，无论层级多深
        print(f"\n📦 Scanning package: {agents.__name__}")
        # 使用pkgutil.walk_packages遍历agents包下的所有模块
        # path参数指定要搜索的路径，这里使用agents包的__path__属性，它包含了包的所有搜索路径
        # prefix参数指定模块名称的前缀，这里使用agents包的完整名称作为前缀，确保导入的模块名称正确
        for module_info in pkgutil.walk_packages(path=agents.__path__, prefix=agents.__name__ + '.'):
            try:
                # print(f"\n📂 Found module: {module_info.name}")
                # 动态导入找到的模块
                module = importlib.import_module(module_info.name)
                
                # 遍历模块中的所有属性
                # print(f"🔍 Inspecting module attributes...")
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    
                    # 检查这个属性是否是一个类，是否是BaseAgent的子类，
                    # 并且不是BaseAgent本身，以避免加载基类
                    if isinstance(attribute, type) and issubclass(attribute, BaseAgent) and attribute is not BaseAgent:
                        # print(f"  Found agent class: {attribute.__name__}")
                        # 实例化Agent
                        agent_instance = attribute()
                        
                        # 检查是否有重名Agent，防止冲突
                        if agent_instance.name in self.agents:
                            print(f"⚠️ Warning: Duplicate agent name '{agent_instance.name}' found. Overwriting.")
                        
                        # 将Agent实例注册到字典中
                        self.agents[agent_instance.name] = agent_instance
                        print(f"  ✅ Registered agent: '{agent_instance.name}' from module {module_info.name}")

            except Exception as e:
                print(f"❌ Error discovering agents in module {module_info.name}: {e}")

    def get_agent(self, name: str) -> BaseAgent | None:
        """根据名称获取一个已注册的Agent实例。"""
        return self.agents.get(name)

    def list_agents(self) -> list[str]:
        """列出所有已注册的Agent名称。"""
        return list(self.agents.keys())

# 创建一个全局单例，应用启动时就会执行
agent_registry = AgentRegistry()