# 🤖 Multi-Agent Platform
[![Made with ❤️](https://img.shields.io/badge/Made%20with-❤️-red.svg)](https://github.com/yourusername/multi_agent_platform)
[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red.svg)](https://streamlit.io)
一个功能强大的多Agent框架对比和测试平台，支持主流AI Agent框架的统一管理、测试和对比。

## 🌟 项目特色

### 🎯 核心功能
- **多框架支持**: 集成 LangChain、LangGraph、CrewAI、OpenAI Agent 等主流框架
- **统一管理**: 提供统一的API接口和Web界面管理所有Agent
- **用户系统**: 完整的用户注册、登录、认证和会话管理
- **MCP工具集成**: 支持Model Context Protocol (MCP) 工具的动态配置和使用
- **实时对话**: 支持多轮对话和会话历史记录
- **可视化界面**: 基于Streamlit的现代化Web界面

### 🔧 技术特性
- **前后端分离**: FastAPI后端 + Streamlit前端
- **动态发现**: 自动发现和注册项目中的Agent实例
- **数据持久化**: MongoDB数据库存储用户和会话数据
- **安全认证**: JWT Token认证和本地存储缓存
- **配置管理**: 支持MCP工具的可视化配置和管理
- **扩展性强**: 易于添加新的Agent框架和工具

## 🏗️ 项目架构

```
multi_agent_platform/
├── backend/                    # 🔧 后端服务
│   ├── agents/                # 🤖 Agent实现
│   │   ├── base_agent.py      # Agent基类定义
│   │   ├── LangChain/         # LangChain框架实现
│   │   ├── LangGraph/         # LangGraph框架实现
│   │   ├── crewAI/            # CrewAI框架实现
│   │   └── OpenAI Agent/      # OpenAI Agent实现
│   ├── api/                   # 🌐 API路由
│   │   └── v1/                # API版本控制
│   ├── core/                  # 🎯 核心功能
│   │   └── agent_registry.py  # Agent注册中心
│   └── main.py                # FastAPI应用入口
├── frontend/                   # 🎨 前端界面
│   ├── app.py                 # Streamlit主应用
│   ├── auth.py                # 用户认证模块
│   └── config.json            # 前端配置文件
├── mcp_server/                # 🛠️ MCP工具服务器
│   ├── weather_server.py      # 天气查询工具
│   ├── math_server.py         # 数学计算工具
│   └── search_server.py       # 搜索工具
├── config.json                # 🔧 MCP工具配置
├── pyproject.toml             # 📦 项目依赖配置
├── Makefile                   # 🚀 构建脚本
└── README.md                  # 📖 项目文档
```

## 🚀 快速开始

### 📋 环境要求

- **Python**: 3.13+
- **包管理器**: UV (推荐) 或 pip
- **数据库**: MongoDB (用于用户和会话数据)
- **API密钥**: OpenAI API Key (用于AI模型调用)

### 🔧 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd multi_agent_platform
```

2. **安装依赖**
```bash
# 使用UV (推荐)
uv sync

# 或使用pip
pip install -e .
```

3. **环境配置**
```bash
# 创建环境变量文件
cp .env.example .env

# 编辑.env文件，添加必要的配置
# OPENAI_API_KEY=your_openai_api_key
# MONGODB_URL=mongodb://localhost:27017
```

4. **启动服务**
```bash
# 使用Makefile一键启动 (推荐)
make run

# 或手动启动
# 启动后端
cd backend && uv run -- uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动前端 (新终端)
cd frontend && uv run -- streamlit run app.py --server.port 8502
```

### 🌐 访问地址

- **前端界面**: http://localhost:8502
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📚 使用指南

### 👤 用户系统

1. **注册账户**: 在前端界面注册新用户账户
2. **登录系统**: 使用用户名和密码登录
3. **会话管理**: 创建、切换和删除对话会话
4. **自动缓存**: 登录状态自动保存，刷新页面无需重新登录

### 🤖 Agent配置

1. **选择框架**: 在侧边栏选择要使用的Agent框架
2. **选择Agent**: 选择具体的Agent实例
3. **配置模型**: 选择模型提供商和具体模型
4. **开始对话**: 在主界面输入消息开始对话

### 🛠️ MCP工具配置

1. **添加工具**: 在MCP配置区域添加新的工具服务器
2. **配置参数**: 设置工具的URL和传输协议
3. **应用设置**: 保存配置并重启服务
4. **工具使用**: Agent可以自动调用配置的工具

### 🔧 添加新Agent

1. **创建目录**: 在`backend/agents/`下创建新框架目录
2. **实现Agent**: 继承`BaseAgent`类实现你的Agent
```python
from agents.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    @property
    def framework(self) -> str:
        return "MyFramework"
    
    @property
    def name(self) -> str:
        return "my_custom_agent"
    
    @property
    def display_name(self) -> str:
        return "我的自定义Agent"
    
    @property
    def description(self) -> str:
        return "这是一个自定义的Agent实现"
    
    async def run(self, message: str, model: str, conversation_id: str) -> str:
        # 实现你的Agent逻辑
        return f"处理结果: {message}"
```
3. **自动注册**: 系统会自动发现并注册新的Agent

## 🔌 API接口

### 📊 获取配置信息
```http
GET /config
```
返回所有可用的框架、Agent和模型配置信息。

### 💬 Agent对话
```http
POST /chat
Content-Type: application/json

{
    "agent_name": "langchain_test_agent",
    "model": "gpt-4",
    "user_prompt": "你好，请介绍一下自己",
    "conversation_id": "conv_123"
}
```

### 🏥 健康检查
```http
GET /health
```
检查后端服务状态。

## 📦 主要依赖

### 🔧 后端依赖
- **FastAPI**: 现代化的Web API框架
- **LangChain**: AI应用开发框架
- **LangGraph**: 状态图AI应用框架
- **CrewAI**: 多Agent协作框架
- **PyMongo**: MongoDB Python驱动
- **PyJWT**: JWT Token处理
- **MCP**: Model Context Protocol支持

### 🎨 前端依赖
- **Streamlit**: 快速Web应用开发框架
- **Requests**: HTTP请求库
- **BCrypt**: 密码加密库

### 🛠️ 工具依赖
- **OpenAI**: OpenAI API客户端
- **Tavily**: 搜索API
- **AgentOps**: Agent操作监控

## 🧪 测试Agent

项目包含多个测试Agent用于验证框架功能：

- **LangChain测试Agent**: 验证LangChain框架集成
- **LangGraph测试Agent**: 验证LangGraph状态图功能
- **CrewAI测试Agent**: 验证CrewAI多Agent协作
- **OpenAI Agent测试**: 验证OpenAI Agent功能

## 🛠️ 开发工具

### 🚀 Makefile命令
```bash
make run      # 启动前后端服务
make backend  # 仅启动后端服务
make frontend # 仅启动前端服务
make stop     # 停止所有服务
```

### 🔧 开发模式
- 后端支持热重载，代码修改后自动重启
- 前端支持实时预览，界面修改即时生效
- 使用UV包管理器提供更快的依赖安装

## 🤝 贡献指南

我们欢迎所有形式的贡献！请遵循以下步骤：

1. **Fork项目** 🍴
2. **创建特性分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送分支** (`git push origin feature/AmazingFeature`)
5. **创建Pull Request** 🔄

### 📝 代码规范
- 遵循PEP 8 Python代码规范
- 添加适当的注释和文档字符串
- 确保新功能包含相应的测试
- 更新相关文档

## 🗺️ 开发路线图

### 🎯 近期计划
- [ ] 添加更多AI Agent框架支持 (AutoGen, Semantic Kernel等)
- [ ] 实现Agent性能对比和评估功能
- [ ] 添加对话导出和分享功能
- [ ] 支持自定义模型配置和管理
- [ ] 实现Agent配置的可视化编辑器

### 🚀 长期目标
- [ ] 支持分布式Agent部署
- [ ] 添加Agent工作流编排功能
- [ ] 实现多租户和权限管理
- [ ] 支持插件系统和第三方扩展
- [ ] 添加监控和日志分析功能

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 📧 **提交Issue**: [GitHub Issues](../../issues)
- 💬 **参与讨论**: [GitHub Discussions](../../discussions)
- 🐛 **报告Bug**: [Bug Report Template](../../issues/new?template=bug_report.md)
- ✨ **功能请求**: [Feature Request Template](../../issues/new?template=feature_request.md)

---

<div align="center">

**🎉 Happy Coding! 让我们一起构建更智能的AI Agent平台！ 🚀**



</div>