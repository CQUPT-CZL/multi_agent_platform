# 多 Agent 框架对比平台 🚀

一个用于对比和测试不同 AI Agent 框架的综合平台，支持 LangChain、CrewAI 等主流框架。

## 📋 项目概述

本项目提供了一个统一的平台来测试和对比不同的 AI Agent 框架，帮助开发者选择最适合的框架。平台采用前后端分离架构，支持动态加载和管理多种 Agent 框架。

### 🎯 主要特性

- **多框架支持**: 支持 LangChain、CrewAI 等主流 AI Agent 框架
- **动态发现**: 自动发现和注册项目中的 Agent 实例
- **统一接口**: 提供统一的 API 接口调用不同框架的 Agent
- **实时对比**: 支持同时测试多个框架的性能和效果
- **友好界面**: 基于 Streamlit 的直观 Web 界面
- **可扩展性**: 易于添加新的 Agent 框架和实例

## 🏗️ 项目架构

```
multi_agent_platform/
├── backend/                 # 后端服务
│   ├── agents/             # Agent 实现
│   │   ├── base_agent.py   # Agent 基类
│   │   ├── LangChain/      # LangChain 框架实现
│   │   └── crewAI/         # CrewAI 框架实现
│   ├── api/                # API 路由
│   │   └── v1/
│   │       ├── router.py   # 主路由
│   │       └── endpoints/  # 具体接口实现
│   ├── core/               # 核心功能
│   │   └── agent_registry.py  # Agent 注册中心
│   └── main.py             # FastAPI 应用入口
├── frontend/               # 前端界面
│   └── app.py              # Streamlit 应用
├── pyproject.toml          # 项目依赖配置
└── README.md               # 项目说明
```

## 🚀 快速开始

### 环境要求

- Python 3.13+
- UV 包管理器（推荐）或 pip

### 安装依赖

使用 UV（推荐）：
```bash
uv sync
```

或使用 pip：
```bash
pip install -r requirements.txt
```

### 启动后端服务

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 `http://localhost:8000` 启动。

### 启动前端界面

```bash
cd frontend
streamlit run app.py
```

前端界面将在 `http://localhost:8501` 启动。

### 访问 API 文档

启动后端后，可以访问自动生成的 API 文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔧 使用指南

### 添加新的 Agent 框架

1. 在 `backend/agents/` 目录下创建新的框架文件夹
2. 继承 `BaseAgent` 类实现你的 Agent
3. 确保包含 `__init__.py` 文件
4. 系统会自动发现并注册新的 Agent

示例 Agent 实现：

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
        return "我的自定义 Agent"
    
    @property
    def description(self) -> str:
        return "这是一个自定义的 Agent 实现"
    
    async def run(self, message: str, model: str, conversation_id: str) -> str:
        # 实现你的 Agent 逻辑
        return f"处理结果: {message}"
```

### API 接口说明

#### 获取配置信息
```http
GET /config
```

返回所有可用的框架和 Agent 配置信息。

#### 与 Agent 对话
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

### 健康检查
```http
GET /health
```

检查后端服务状态。

## 🧪 测试

项目包含了测试用的 Agent 实现：

- **LangChain 测试 Agent**: 测试 LangChain 框架的连通性和基本功能
- **CrewAI 测试 Agent**: 测试 CrewAI 框架的功能（待实现）

## 📦 依赖包

主要依赖：
- **FastAPI**: 后端 API 框架
- **Streamlit**: 前端界面框架
- **LangChain**: AI Agent 框架
- **Uvicorn**: ASGI 服务器

完整依赖列表请查看 `pyproject.toml` 文件。

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 开发计划

- [ ] 添加更多 AI Agent 框架支持
- [ ] 实现 Agent 性能对比功能
- [ ] 添加用户认证和权限管理
- [ ] 支持自定义模型配置
- [ ] 添加对话历史记录
- [ ] 实现 Agent 配置的可视化编辑


## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发起 Discussion

---

**Happy Coding! 🎉**