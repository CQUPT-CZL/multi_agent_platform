# 导入 FastAPI 的 APIRouter
from fastapi import APIRouter

# 从同级目录下的 'endpoints' 文件夹中，导入我们定义好的各个路由模块
# 我们为每个功能（如 config, chat）都创建了一个独立的路由
from .endpoints import config, chat

# 创建一个 APIRouter 实例，这就是我们将要导出的“路由中心”
api_router = APIRouter()

# =============================================================================
# 聚合所有子路由
# =============================================================================
# 使用 .include_router() 方法将各个子路由模块包含进来。
#
# - 第一个参数是子路由模块中定义的 router 实例。
# - `tags` 参数非常有用，它会在 FastAPI 自动生成的API文档 (/docs) 中
#   为这组接口进行分组，让文档看起来更清晰。

# 包含来自 config.py 的路由，并将其标记为 "System & Config"
api_router.include_router(config.router, tags=["System & Config"])

# 包含来自 chat.py 的路由，并将其标记为 "Agent Interaction"
api_router.include_router(chat.router, tags=["Agent Interaction"])

# 您未来添加任何新的功能模块（比如 users.py, analytics.py），
# 只需在这里加一行 .include_router() 即可，非常方便扩展！
