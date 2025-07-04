module.exports = {
    apps: [
      {
        // --- 后端应用配置 ---
        name: "multi-agent-backend",
        script: "/home/czl/.local/bin/uv", // 运行的命令 (uv的绝对路径)
        args: "run uvicorn backend.main:app --host 0.0.0.0 --port 8000", // 命令的参数
        cwd: "~/project/multi-agent-platform/", // ‼️【重要】命令执行的工作目录 (项目根目录)
        interpreter: "none", // 告诉pm2这不是一个node.js脚本，直接执行即可
        env: {
          "PYTHONPATH": "." // 确保能找到backend目录
        }
      },
      {
        // --- 前端应用配置 ---
        name: "multi-agent-frontend",
        script: "/home/czl/.local/bin/uv", // 同样使用uv
        args: "run streamlit run app.py --server.port 8502",
        cwd: "~/project/multi-agent-platform/frontend/", // ‼️【重要】前端的工作目录
        interpreter: "none",
      }
    ]
  };
  