# 导入所有必要的库
import streamlit as st
import requests
from datetime import datetime
import json
import os
from auth import check_authentication, render_login_page, render_user_info, check_login_required

# 设置页面配置
st.set_page_config(
    page_title="Multi-Agent 测试平台",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    /* 主题色彩 */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --accent-color: #f093fb;
        --success-color: #4CAF50;
        --warning-color: #ff9800;
        --error-color: #f44336;
        --background-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --card-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        --border-radius: 12px;
    }
    
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 主容器样式 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    /* 侧边栏美化 */
    .css-1d391kg {
        background: var(--background-gradient);
        border-radius: 0 var(--border-radius) var(--border-radius) 0;
    }
    
    /* 标题样式 */
    .main-title {
        background: var(--background-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
        animation: fadeInDown 1s ease-out;
    }
    
    /* 配置卡片样式 */
    .config-card {
        background: white;
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--card-shadow);
        border-left: 4px solid var(--primary-color);
        margin-bottom: 1rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .config-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    /* 状态指示器 */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    .status-online {
        background-color: var(--success-color);
    }
    
    .status-offline {
        background-color: var(--error-color);
    }
    
    /* 按钮美化 */
    .stButton > button {
        background: var(--background-gradient);
        color: white;
        border: none;
        border-radius: var(--border-radius);
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: var(--card-shadow);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* 聊天消息样式 */
    .stChatMessage {
        background: white;
        border-radius: var(--border-radius);
        box-shadow: var(--card-shadow);
        margin-bottom: 1rem;
        animation: slideInUp 0.5s ease-out;
    }
    
    /* 输入框样式 */
    .stTextInput > div > div > input {
        border-radius: var(--border-radius);
        border: 2px solid #e0e0e0;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* 选择框样式 */
    .stSelectbox > div > div {
        border-radius: var(--border-radius);
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div {
        background: var(--background-gradient);
        border-radius: var(--border-radius);
    }
    
    /* 成功/错误消息样式 */
    .stSuccess {
        background-color: rgba(76, 175, 80, 0.1);
        border-left: 4px solid var(--success-color);
        border-radius: var(--border-radius);
    }
    
    .stError {
        background-color: rgba(244, 67, 54, 0.1);
        border-left: 4px solid var(--error-color);
        border-radius: var(--border-radius);
    }
    
    .stWarning {
        background-color: rgba(255, 152, 0, 0.1);
        border-left: 4px solid var(--warning-color);
        border-radius: var(--border-radius);
    }
    
    .stInfo {
        background-color: rgba(102, 126, 234, 0.1);
        border-left: 4px solid var(--primary-color);
        border-radius: var(--border-radius);
    }
    
    /* 动画效果 */
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
        100% {
            opacity: 1;
        }
    }
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        
        .config-card {
            padding: 1rem;
        }
    }
    
    /* 工具提示样式 */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: white;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 0. MCP配置管理
# =============================================================================
# config.json file path setting
CONFIG_FILE_PATH = "config.json"

# Function to load settings from JSON file
def load_config_from_json():
    """
    Loads settings from config.json file.
    Creates a file with default settings if it doesn't exist.

    Returns:
        dict: Loaded settings
    """
    default_config = {
        "weather": {
                "url": "http://localhost:8005/mcp/",
                "transport": "streamable-http"
            }
    }
    
    try:
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Create file with default settings if it doesn't exist
            save_config_to_json(default_config)
            return default_config
    except Exception as e:
        st.error(f"Error loading settings file: {str(e)}")
        return default_config

# Function to save settings to JSON file
def save_config_to_json(config):
    """
    Saves settings to config.json file.

    Args:
        config (dict): Settings to save
    
    Returns:
        bool: Save success status
    """
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving settings file: {str(e)}")
        return False


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
# 3. 页面基础设置和Session State初始化
# =============================================================================
# 页面配置已在文件开头设置

# =============================================================================
# 用户认证检查
# =============================================================================
# 检查是否需要登录以及用户认证状态
if check_login_required():
    if not check_authentication():
        render_login_page()
        st.stop()  # 阻止页面继续渲染
    else:
        # 用户已登录，在侧边栏显示用户信息
        render_user_info()
        
        # 初始化会话管理
        if "current_session_id" not in st.session_state:
            st.session_state.current_session_id = None
        if "session_messages" not in st.session_state:
            st.session_state.session_messages = []

# 初始化MCP配置相关的session state
if "mcp_config_initialized" not in st.session_state:
    st.session_state.mcp_config_initialized = False
    st.session_state.mcp_tools_expander = False
    # 加载现有配置作为pending配置
    loaded_config = load_config_from_json()
    st.session_state.pending_mcp_config = loaded_config.copy()
    st.session_state.current_mcp_config = loaded_config.copy()
    st.session_state.mcp_config_initialized = True


# =============================================================================
# 4. 侧边栏 (Sidebar) 动态配置区域
# =============================================================================
# 使用 'with' 语句将所有元素放入侧边栏
with st.sidebar:
    # st.markdown('<div class="config-card"><h2 style="margin:0; color: black; text-align: center;">🛠️ 配置中心</h2></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
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
    st.markdown('<div class="status-indicator status-online"></div>**后端连接状态**: 已连接', unsafe_allow_html=True)
    st.success("✅ 已成功从后端加载配置！")
    st.markdown("---")

    # ---- 动态生成选择器 ----

    st.markdown('<div class="config-card"><h3 style="margin:0; color: #667eea;">🤖 Agent配置</h3></div>', unsafe_allow_html=True)
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
        options=["DeepSeek", "本地模型"],
        help="模型的性能会直接影响 Agent 的表现。"
    )
    models = {
        "DeepSeek": ["deepseek-chat"],
        "本地模型": ["llama3-70b-instruct", "mistral-large"]
    }
    selected_model = st.selectbox(
        label="⚙️ **第四步：选择具体模型**",
        options=models[model_provider]
    )

    st.markdown("---")
    
    # =============================================================================
    # MCP工具配置部分
    # =============================================================================
    st.markdown('<div class="config-card"><h3 style="margin:0; color: #667eea;">🔧 MCP工具配置</h3></div>', unsafe_allow_html=True)
    
    # MCP工具添加界面
    with st.expander("🧰 添加MCP工具", expanded=st.session_state.mcp_tools_expander):
        st.markdown(
            """
        请以JSON格式插入**一个工具**。
        
        ⚠️ **重要**: JSON必须用大括号(`{}`)包装。
        """
        )
        
        # 提供示例
        example_json = {
            "weather": {
                "url": "http://localhost:8005/mcp/",
                "transport": "streamable_http"
            }
        }
        
        default_text = json.dumps(example_json, indent=2, ensure_ascii=False)
        
        new_tool_json = st.text_area(
            "工具JSON配置",
            default_text,
            height=200,
        )
        
        # 添加工具按钮
        if st.button(
            "添加工具",
            type="primary",
            key="add_tool_button",
            use_container_width=True,
        ):
            try:
                # 验证输入
                if not new_tool_json.strip().startswith(
                    "{"
                ) or not new_tool_json.strip().endswith("}"):
                    st.error("JSON必须以大括号开始和结束({})。")
                    st.markdown('正确格式: `{ "tool_name": { ... } }`')
                else:
                    # 解析JSON
                    parsed_tool = json.loads(new_tool_json)
                    
                    # 检查是否为mcpServers格式并相应处理
                    if "mcpServers" in parsed_tool:
                        # 将mcpServers的内容移到顶层
                        parsed_tool = parsed_tool["mcpServers"]
                        st.info(
                            "检测到'mcpServers'格式。自动转换中。"
                        )
                    
                    # 检查输入的工具数量
                    if len(parsed_tool) == 0:
                        st.error("请至少输入一个工具。")
                    else:
                        # 处理所有工具
                        success_tools = []
                        for tool_name, tool_config in parsed_tool.items():
                            # 检查URL字段并设置transport
                            if "url" in tool_config:
                                # 如果存在URL，设置transport为"sse"
                                tool_config["transport"] = "streamable_http"
                                st.info(
                                    f"在'{tool_name}'工具中检测到URL，设置transport为'streamable_http'。"
                                )
                            elif "transport" not in tool_config:
                                # 如果不存在URL且未指定transport，设置默认"stdio"
                                tool_config["transport"] = "stdio"
                            
                            # 检查必需字段
                            if (
                                "command" not in tool_config
                                and "url" not in tool_config
                            ):
                                st.error(
                                    f"'{tool_name}'工具配置需要'command'或'url'字段。"
                                )
                            elif "command" in tool_config and "args" not in tool_config:
                                st.error(
                                    f"'{tool_name}'工具配置需要'args'字段。"
                                )
                            elif "command" in tool_config and not isinstance(
                                tool_config["args"], list
                            ):
                                st.error(
                                    f"'{tool_name}'工具中的'args'字段必须是数组([])格式。"
                                )
                            else:
                                # 添加工具到pending_mcp_config
                                st.session_state.pending_mcp_config[tool_name] = (
                                    tool_config
                                )
                                success_tools.append(tool_name)
                        
                        # 成功消息
                        if success_tools:
                            if len(success_tools) == 1:
                                st.success(
                                    f"{success_tools[0]}工具已添加。点击'应用设置'按钮以应用。"
                                )
                            else:
                                tool_names = ", ".join(success_tools)
                                st.success(
                                    f"总共{len(success_tools)}个工具({tool_names})已添加。点击'应用设置'按钮以应用。"
                                )
                            # 添加后折叠expander
                            st.session_state.mcp_tools_expander = False
                            st.rerun()
                            
            except json.JSONDecodeError as e:
                st.error(f"JSON解析错误: {e}")
                st.markdown(
                    f"""
                **如何修复**:
                1. 检查您的JSON格式是否正确。
                2. 所有键必须用双引号(")包装。
                3. 字符串值也必须用双引号(")包装。
                4. 在字符串中使用双引号时，必须转义(\\)。
                """
                )
            except Exception as e:
                st.error(f"发生错误: {e}")
    
    # 显示已注册工具列表并添加删除按钮
    with st.expander("📋 已注册工具列表", expanded=True):
        try:
            pending_config = st.session_state.pending_mcp_config
        except Exception as e:
            st.error("不是有效的MCP工具配置。")
        else:
            # 遍历pending配置中的键(工具名称)
            for tool_name in list(pending_config.keys()):
                col1, col2 = st.columns([8, 2])
                col1.markdown(f"- **{tool_name}**")
                if col2.button("🗑️", key=f"delete_{tool_name}", help="删除", use_container_width=True):
                    # 从pending配置中删除工具(不立即应用)
                    del st.session_state.pending_mcp_config[tool_name]
                    st.success(
                        f"{tool_name}工具已删除。点击'应用设置'按钮以应用。"
                    )
                    st.rerun()
    
    # 应用设置按钮
    if st.button(
        "应用设置",
        key="apply_button",
        type="primary",
        use_container_width=True,
    ):
        # 显示应用消息
        apply_status = st.empty()
        with apply_status.container():
            st.warning("🔄 正在应用更改。请稍候...")
            progress_bar = st.progress(0)
            
            # 保存设置到config.json文件
            save_result = save_config_to_json(st.session_state.pending_mcp_config)
            if save_result:
                st.session_state.current_mcp_config = st.session_state.pending_mcp_config.copy()
                progress_bar.progress(50)
                st.success("✅ 新设置已应用并保存到config.json。")
                # 折叠工具添加expander
                if "mcp_tools_expander" in st.session_state:
                    st.session_state.mcp_tools_expander = False
            else:
                st.error("❌ 保存设置文件失败。")
            
            progress_bar.progress(100)
        
        # 刷新页面
        st.rerun()
    
    st.markdown("---")
    
    # 历史会话管理（仅在用户登录时显示）
    if check_login_required() and check_authentication():
        st.markdown('<div class="config-card"><h3 style="margin:0; color: #667eea;">💬 会话管理</h3></div>', unsafe_allow_html=True)
        
        # 获取当前用户名和认证管理器
        username = st.session_state.get("username")
        auth_manager = st.session_state.get("auth_manager")
        
        if username and auth_manager:
            # 新建会话按钮
            if st.button("🆕 新建会话", use_container_width=True):
                # 创建新会话
                new_session_id = auth_manager.create_chat_session(username)
                if new_session_id:
                    st.session_state.current_session_id = new_session_id
                    st.session_state.session_messages = []
                    st.session_state.messages = [
                        {"role": "assistant", "content": "您好！请在左侧配置好您想测试的组合，然后在这里向我提问吧！"}
                    ]
                    st.rerun()
            
            # 刷新按钮和历史会话标题
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("**历史会话:**")
            with col2:
                if st.button("🔄", help="刷新会话列表", use_container_width=True):
                    st.rerun()
            
            # 获取用户的会话列表
            sessions = auth_manager.get_user_chat_sessions(username, limit=10)
            
            if sessions:
                for session in sessions:
                    session_id = session["session_id"]
                    title = session["title"]
                    updated_at = session["updated_at"]
                    
                    # 格式化时间显示
                    time_str = updated_at.strftime("%m-%d %H:%M")
                    
                    # 会话选择按钮
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        # 当前会话高亮显示
                        button_type = "primary" if session_id == st.session_state.current_session_id else "secondary"
                        if st.button(f"📝 {title}", key=f"session_{session_id}", 
                                   help=f"更新时间: {time_str}", use_container_width=True, type=button_type):
                            # 加载选中的会话
                            session_data = auth_manager.get_chat_session(session_id, username)
                            if session_data:
                                st.session_state.current_session_id = session_id
                                # 将数据库中的消息转换为streamlit格式
                                messages = [{"role": msg["role"], "content": msg["content"]} 
                                           for msg in session_data.get("messages", [])]
                                if not messages:
                                    messages = [
                                        {"role": "assistant", "content": "您好！请在左侧配置好您想测试的组合，然后在这里向我提问吧！"}
                                    ]
                                st.session_state.messages = messages
                                st.rerun()
                    
                    with col2:
                        if st.button("🗑️", key=f"delete_{session_id}", help="删除会话", use_container_width=True):
                            if auth_manager.delete_chat_session(session_id, username):
                                if session_id == st.session_state.current_session_id:
                                    st.session_state.current_session_id = None
                                    st.session_state.messages = [
                                        {"role": "assistant", "content": "您好！请在左侧配置好您想测试的组合，然后在这里向我提问吧！"}
                                    ]
                                st.success("会话已删除")
                                st.rerun()
            else:
                st.info("暂无历史会话")
        
        st.markdown("---")
    
    # =============================================================================
    # 系统信息显示
    # =============================================================================
    # =============================================================================
    # 操作按钮
    # =============================================================================
    st.markdown('<div class="config-card"><h3 style="margin:0; color: #667eea;">🔄 操作</h3></div>', unsafe_allow_html=True)
    
    # 刷新按钮，用于清除缓存并重新从后端拉取配置
    if st.button("🔄 刷新配置", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # 清除聊天记录按钮
    if st.button("🗑️ 清除聊天记录", use_container_width=True):
        if "messages" in st.session_state:
            del st.session_state.messages
        st.rerun()
    
    # 重置MCP配置按钮
    if st.button("🔧 重置MCP配置", use_container_width=True):
        # 重置为默认配置
        default_config = {
            "weather": {
                "url": "http://localhost:8005/mcp/",
                "transport": "streamable-http"
            }
        }
        st.session_state.pending_mcp_config = default_config.copy()
        st.session_state.current_mcp_config = default_config.copy()
        save_config_to_json(default_config)
        st.success("✅ MCP配置已重置为默认设置")
        st.rerun()


# =============================================================================
# 5. 主聊天界面
# =============================================================================
# 使用自定义样式的标题
st.markdown('<h1 class="main-title">🚀 Multi-Agent 测试平台</h1>', unsafe_allow_html=True)

# 在标题下方显示当前用户的选择，使用美化的配置卡片
mcp_tool_count = len(st.session_state.current_mcp_config) if "current_mcp_config" in st.session_state else 0

# 创建配置状态卡片
config_html = f"""
<div class="config-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; margin-bottom: 2rem;">
    <h3 style="margin: 0 0 1rem 0; color: white;">📊 当前配置状态</h3>
    <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 1rem;">
        <div style="flex: 1; min-width: 200px;">
            <div style="font-size: 0.9rem; opacity: 0.8;">Agent框架</div>
            <div style="font-size: 1.1rem; font-weight: 600;">{selected_framework}</div>
        </div>
        <div style="flex: 1; min-width: 200px;">
            <div style="font-size: 0.9rem; opacity: 0.8;">Agent名称</div>
            <div style="font-size: 1.1rem; font-weight: 600;">{selected_agent_name}</div>
        </div>
        <div style="flex: 1; min-width: 200px;">
            <div style="font-size: 0.9rem; opacity: 0.8;">模型</div>
            <div style="font-size: 1.1rem; font-weight: 600;">{selected_model}</div>
        </div>
        <div style="flex: 1; min-width: 200px;">
            <div style="font-size: 0.9rem; opacity: 0.8;">MCP工具</div>
            <div style="font-size: 1.1rem; font-weight: 600;">{mcp_tool_count} 个</div>
        </div>
    </div>
</div>
"""
st.markdown(config_html, unsafe_allow_html=True)

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
if prompt := st.chat_input("💭 请输入您的问题或指令..."):
    # 确保有当前会话（如果用户登录了）
    if check_login_required() and check_authentication():
        username = st.session_state.get("username")
        auth_manager = st.session_state.get("auth_manager")
        
        # 如果没有当前会话，创建一个新会话
        if not st.session_state.current_session_id and username and auth_manager:
            new_session_id = auth_manager.create_chat_session(username)
            if new_session_id:
                st.session_state.current_session_id = new_session_id
    
    # 1. 将用户的输入添加到聊天记录并显示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 保存用户消息到数据库
    if (check_login_required() and check_authentication() and 
        st.session_state.current_session_id and 
        st.session_state.get("auth_manager")):
        
        auth_manager = st.session_state.auth_manager
        agent_config = {
            "framework": selected_framework,
            "agent_name": selected_agent_name,
            "model": selected_model
        }
        
        auth_manager.save_message_to_session(
            st.session_state.current_session_id,
            "user",
            prompt,
            agent_config
        )

    # 2. 调用后端 API 并显示 Agent 的响应
    with st.chat_message("assistant"):
        # 使用美化的思考中提示
        message_placeholder = st.empty()
        thinking_html = """
        <div style="
            padding: 1.5rem;
            border-radius: 12px; 
            text-align: center;
            animation: pulse 2s infinite;
        ">
            <div style="color: #666; font-size: 0.9rem; margin-bottom: 1rem;">
                正在分析您的问题并生成回答
            </div>
            <div>
                <div style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; 
                    background: #667eea; margin: 0 2px; animation: pulse 1.5s infinite;">
                </div>
                <div style="display: inline-block; width: 8px; height: 8px; border-radius: 50%;
                    background: #667eea; margin: 0 2px; animation: pulse 1.5s infinite 0.2s;">
                </div>
                <div style="display: inline-block; width: 8px; height: 8px; border-radius: 50%;
                    background: #667eea; margin: 0 2px; animation: pulse 1.5s infinite 0.4s;">
                </div>
            </div>
        </div>
        """
        message_placeholder.markdown(thinking_html, unsafe_allow_html=True)
        
        try:
            # 准备发送给后端 /chat 接口的数据
            chat_payload = {
                "agent_name": selected_agent_name,  # 从侧边栏动态获取
                "model": selected_model,
                "message": st.session_state.messages[-10:], # 只保留最近的10条消息记录
                "conversation_id": st.session_state.current_session_id or f"st_conv_{datetime.now().timestamp()}"
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
                # 直接显示响应内容，不使用HTML包装
                message_placeholder.markdown(agent_response)
            else:
                # 美化错误响应
                error_html = f"""
                <div style="
                    padding: 1.5rem;
                    background: rgba(244, 67, 54, 0.1);
                    border-radius: 12px;
                    border-left: 4px solid #f44336;
                    margin: 1rem 0;
                ">
                    <div style="color: #f44336; font-weight: 600; margin-bottom: 1rem; display: flex; align-items: center;">
                        <span style="margin-right: 0.5rem;">❌</span>
                        API 调用失败
                    </div>
                    <div style="color: #666; margin-bottom: 0.5rem;"><strong>状态码:</strong> {response.status_code}</div>
                    <div style="color: #666;"><strong>错误信息:</strong> {response.text}</div>
                </div>
                """
                message_placeholder.markdown(error_html, unsafe_allow_html=True)
                agent_response = f"❌ **API 调用失败**\n\n- **状态码**: {response.status_code}\n- **错误信息**: {response.text}"
        
        except requests.exceptions.RequestException as e:
            # 美化网络错误
            error_html = f"""
            <div style="
                padding: 1.5rem;
                background: rgba(244, 67, 54, 0.1);
                border-radius: 12px;
                border-left: 4px solid #f44336;
                margin: 1rem 0;
            ">
                <div style="color: #f44336; font-weight: 600; margin-bottom: 1rem; display: flex; align-items: center;">
                    <span style="margin-right: 0.5rem;">🌐</span>
                    网络请求失败
                </div>
                <div style="color: #666; margin-bottom: 0.5rem;"><strong>错误类型:</strong> {type(e).__name__}</div>
                <div style="color: #666; margin-bottom: 1rem;"><strong>详情:</strong> {str(e)}</div>
                <div style="color: #888; font-size: 0.9rem; font-style: italic;">请检查您的网络连接以及后端服务是否正常。</div>
            </div>
            """
            message_placeholder.markdown(error_html, unsafe_allow_html=True)
            agent_response = f"❌ **网络请求失败**\n\n- **错误类型**: {type(e).__name__}\n- **详情**: {str(e)}\n\n请检查您的网络连接以及后端服务是否正常。"
        
        # 3. 将 Agent 的完整响应也添加到聊天记录中
        st.session_state.messages.append({"role": "assistant", "content": agent_response})
        
        # 保存助手响应到数据库
        if (check_login_required() and check_authentication() and 
            st.session_state.current_session_id and 
            st.session_state.get("auth_manager")):
            
            auth_manager = st.session_state.auth_manager
            auth_manager.save_message_to_session(
                st.session_state.current_session_id,
                "assistant",
                agent_response
            )
