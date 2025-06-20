from fastapi import FastAPI
# 导入我们刚刚创建的聚合路由
from api.v1.router import api_router

# 初始化 FastAPI 应用
app = FastAPI(
    title="多 Agent 框架对比平台后端",
    description="一个为多Agent框架对比平台提供支持的强大后端服务。🚀",
    version="1.0.0"
)

# =============================================================================
# 包含主路由
# =============================================================================
# 只需要这一行代码，就可以将 api_router 中聚合的所有路由
# (包括 /config 和 /chat) 全部注册到我们的 FastAPI 应用中。
# 所有路由都会在根路径下可用 (例如: http://localhost:8000/config)
app.include_router(api_router)


# 如果您未来想做API版本控制，可以这样做：
# app.include_router(api_router, prefix="/v1")
# 这样所有接口的路径都会变成 /v1/config, /v1/chat 等。


# 健康检查接口 (放在主文件里没问题，因为它很简单)
@app.get("/health", tags=["System & Config"])
def health_check():
    """
    检查后端服务是否正在运行。
    """
    return {"status": "ok", "message": "后端服务一切正常！✅"}

