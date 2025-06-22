# 导入所有必要的库
import streamlit as st
import requests
from datetime import datetime

# =============================================================================
# 1. 后端 API 配置
# =============================================================================
# 您后端 FastAPI 服务运行的地址。
# 如果您在Docker等容器化环境中运行，可能需要将其更改为服务名称，例如 "http://backend:8000"
API_BASE_URL = "http://localhost:8000"


# =============================================================================
# 2. 后端数据获取与缓存
# =============================================================================
@st.cache_data(ttl=300)  # 缓存5分钟，避免每次刷新都请求后端，提高性能
def get_backend_config():
    """
    从后端获取并缓存框架和Agent的配置信息。
    这是实现前端动态化的核心函数。

    Returns:
        tuple: (是否成功, 配置数据或错误信息字典)
    """
    try:
        # 向后端 /config 接口发送 GET 请求
        response = requests.get(f"{API_BASE_URL}/config", timeout=5)
        
        # 检查HTTP响应状态码
        if response.status_code == 200:
            # 如果成功，返回True和解析后的JSON数据
            return True, response.json()
        else:
            # 如果服务器返回错误码，返回False和错误详情
            error_details = f"获取配置失败，状态码: {response.status_code}. 响应内容: {response.text}"
            return False, {"error": error_details}
            
    except requests.exceptions.ConnectionError:
        # 如果无法连接到服务器，返回连接错误信息
        return False, {"error": "无法连接到后端服务。请确保后端正在运行。"}
    except requests.exceptions.Timeout:
        # 如果请求超时，返回超时错误信息
        return False, {"error": "请求后端配置超时。"}
    except Exception as e:
        # 捕获其他所有未知异常
        return False, {"error": f"获取配置时发生未知错误: {str(e)}"}


# =============================================================================
# 3. 页面基础设置
# =============================================================================
# 配置浏览器标签页的标题、图标和页面布局
st.set_page_config(
    page_title="多 Agent 框架对比平台",
    page_icon="�",
    layout="wide"
)


# =============================================================================
# 4. 侧边栏 (Sidebar) 动态配置区域
# =============================================================================
# 使用 'with' 语句将所有元素放入侧边栏
with st.sidebar:
    st.title("🛠️ 配置中心")
    
    # 调用函数获取后端配置
    config_ok, backend_config = get_backend_config()

    # 如果获取配置失败，则显示错误信息和重连选项
    if not config_ok:
        st.error(f"❌ 无法加载后端配置:\n{backend_config['error']}")
        st.info("💡 请确保后端服务已启动并运行在 http://localhost:8000")
        
        # 添加重新连接按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 重新连接后端", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("🗑️ 清除所有缓存", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        st.markdown("---")
        st.markdown("**故障排除提示：**")
        st.markdown("- 检查后端服务是否在 http://localhost:8000 运行")
        st.markdown("- 尝试重启后端服务")
        st.markdown("- 检查防火墙设置")
        st.markdown("- 确认端口8001未被其他程序占用")
        
        # 终止脚本执行，但用户可以通过按钮重新触发
        st.stop()

    # 如果成功，显示一个友好的成功状态
    st.success("✅ 已成功从后端加载配置！")
    st.markdown("---")

    # ---- 动态生成选择器 ----

    # 1. Agent框架选择器
    # 选项的 keys 直接来自后端返回的 JSON 数据
    framework_options = list(backend_config.keys())
    selected_framework = st.selectbox(
        label="🤖 **第一步：选择 Agent 框架**",
        options=framework_options
    )

    # 2. Agent/任务选择器
    # 根据上一步选择的框架，动态地获取该框架下的所有可用 Agent
    agent_options_list = backend_config[selected_framework]
    
    # 使用 format_func 来实现"显示友好名称，返回技术名称"的绝佳用户体验
    # 这对于调用 API 至关重要，因为 API 需要的是唯一的技术名称 (name)
    selected_agent_name = st.selectbox(
        label="🎯 **第二步：选择具体 Agent (任务)**",
        options=[agent['name'] for agent in agent_options_list],  # 内部值是技术名称
        # 将技术名称(name)映射为显示名称(display_name)
        format_func=lambda name: next(
            # 遍历agent列表,找到匹配name的agent并返回其display_name
            (agent['display_name'] for agent in agent_options_list if agent['name'] == name),
            # 如果找不到匹配的agent,则返回原始name作为后备选项
            name  
        )
    )
    
    # 获取并显示当前选中Agent的描述信息
    selected_agent_desc = next(
        (agent['description'] for agent in agent_options_list if agent['name'] == selected_agent_name),
        "暂无描述"  # 如果找不到描述信息，显示默认文本
    )
    st.markdown(f"📝 **Agent描述**:\n\n{selected_agent_desc}")

    # 3. 模型提供商和模型选择器
    # 这部分目前是硬编码的，但也可以改造成从后端动态获取
    model_provider = st.selectbox(
        label="🧠 **第三步：选择模型提供商**",
        options=["OpenAI", "Google", "Anthropic", "本地模型"],
        help="模型的性能会直接影响 Agent 的表现。"
    )
    models = {
        "OpenAI": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "Google": ["gemini-1.5-pro", "gemini-1.0-pro"],
        "Anthropic": ["claude-3-opus", "claude-3-sonnet"],
        "本地模型": ["llama3-70b-instruct", "mistral-large"]
    }
    selected_model = st.selectbox(
        label="⚙️ **第四步：选择具体模型**",
        options=models[model_provider]
    )
    
    st.markdown("---")
    
    # 刷新按钮，用于清除缓存并重新从后端拉取配置
    if st.button("🔄 刷新配置", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# =============================================================================
# 5. 主聊天界面
# =============================================================================
st.title("multi-Agent 测试平台 🚀")
# 在标题下方显示当前用户的选择，非常直观
st.caption(f"当前配置:  `{selected_framework}`  >  `{selected_agent_name}`  >  `{selected_model}`")

# ---- 核心聊天逻辑 ----

# 初始化聊天记录
# 使用 st.session_state 可以在页面重新渲染时保持数据不丢失
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！请在左侧配置好您想测试的组合，然后在这里向我提问吧！"}
    ]

# 显示历史聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 接收用户的新输入
if prompt := st.chat_input("请输入您的问题或指令..."):
    # 1. 将用户的输入添加到聊天记录并显示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 调用后端 API 并显示 Agent 的响应
    with st.chat_message("assistant"):
        # 使用一个占位符，可以先显示“思考中”，然后用真实响应覆盖它
        message_placeholder = st.empty()
        message_placeholder.markdown("🧠 Agent 正在思考中，请稍候...")
        
        try:
            # 准备发送给后端 /chat 接口的数据
            chat_payload = {
                "agent_name": selected_agent_name,  # 从侧边栏动态获取
                "model": selected_model,
                "message": st.session_state.messages[-10:], # 只保留最近的10条消息记录
                "conversation_id": f"st_conv_{datetime.now().timestamp()}"
            }
            
            # 发送 POST 请求
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json=chat_payload,
                timeout=300  # 设置一个较长的超时时间，因为Agent任务可能很耗时
            )

            # 处理响应
            if response.status_code == 200:
                agent_response = response.json().get("response", "抱歉，收到了一个空的响应。")
            else:
                agent_response = f"❌ **API 调用失败**\n\n- **状态码**: {response.status_code}\n- **错误信息**: {response.text}"
        
        except requests.exceptions.RequestException as e:
            agent_response = f"❌ **网络请求失败**\n\n- **错误类型**: {type(e).__name__}\n- **详情**: {str(e)}\n\n请检查您的网络连接以及后端服务是否正常。"
        
        # 更新占位符为最终的响应
        message_placeholder.markdown(agent_response)
        
        # 3. 将 Agent 的完整响应也添加到聊天记录中
        st.session_state.messages.append({"role": "assistant", "content": agent_response})
