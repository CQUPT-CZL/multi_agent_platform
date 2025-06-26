import streamlit as st
import hashlib
import jwt
import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from typing import Optional, Dict, Any
import re
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class AuthManager:
    """用户认证管理器"""
    
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL")
        self.database_name = os.getenv("MONGODB_DATABASE")
        self.collection_name = os.getenv("MONGODB_COLLECTION")
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
        
        # 初始化MongoDB连接
        try:
            self.client = MongoClient(self.mongodb_url)
            print(f"✅ MongoDB连接成功: {self.mongodb_url}")
            self.db = self.client[self.database_name]
            print(f"✅ 数据库 {self.database_name} 已连接")
            self.users_collection = self.db[self.collection_name]
            print(f"✅ 集合 {self.collection_name} 已连接")
            # 创建用户名唯一索引
            self.users_collection.create_index("username", unique=True)
            print(f"✅ 集合 {self.collection_name} 已创建或已存在")
        except Exception as e:
            st.error(f"❌ MongoDB连接失败: {str(e)}")
            self.client = None
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> tuple[bool, str]:
        """验证密码强度"""
        if len(password) < 6:
            return False, "密码长度至少6位"
        if not re.search(r'[A-Za-z]', password):
            return False, "密码必须包含字母"
        if not re.search(r'\d', password):
            return False, "密码必须包含数字"
        return True, "密码符合要求"
    
    def register_user(self, username: str, email: str, password: str) -> tuple[bool, str]:
        """用户注册"""
        if not self.client:
            return False, "数据库连接失败"
        
        # 验证输入
        if not username or len(username) < 3:
            return False, "用户名至少3个字符"
        
        if not self.validate_email(email):
            return False, "邮箱格式不正确"
        
        is_valid, msg = self.validate_password(password)
        if not is_valid:
            return False, msg
        
        try:
            # 检查用户名是否已存在
            if self.users_collection.find_one({"username": username}):
                return False, "用户名已存在"
            
            # 检查邮箱是否已存在
            if self.users_collection.find_one({"email": email}):
                return False, "邮箱已被注册"
            
            # 创建用户
            user_data = {
                "username": username,
                "email": email,
                "password": self.hash_password(password),
                "created_at": datetime.utcnow(),
                "last_login": None
            }
            
            self.users_collection.insert_one(user_data)
            return True, "注册成功！"
            
        except Exception as e:
            return False, f"注册失败: {str(e)}"
    
    def login_user(self, username: str, password: str) -> tuple[bool, str, Optional[str]]:
        """用户登录"""
        if not self.client:
            return False, "数据库连接失败", None
        
        try:
            # 查找用户
            user = self.users_collection.find_one({"username": username})
            if not user:
                return False, "用户名不存在", None
            
            # 验证密码
            if user["password"] != self.hash_password(password):
                return False, "密码错误", None
            
            # 更新最后登录时间
            self.users_collection.update_one(
                {"username": username},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            # 生成JWT令牌
            token = self.generate_token(username)
            return True, "登录成功！", token
            
        except Exception as e:
            return False, f"登录失败: {str(e)}", None
    
    def generate_token(self, username: str) -> str:
        """生成JWT令牌"""
        payload = {
            "username": username,
            "exp": datetime.utcnow() + timedelta(minutes=self.jwt_expire_minutes),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_token(self, token: str) -> tuple[bool, Optional[str]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            username = payload.get("username")
            return True, username
        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.InvalidTokenError:
            return False, None
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        if not self.client:
            return None
        
        try:
            user = self.users_collection.find_one(
                {"username": username},
                {"password": 0}  # 不返回密码字段
            )
            return user
        except Exception:
            return None


def check_login_required() -> bool:
    """检查是否需要登录"""
    return os.getenv("REQUIRE_LOGIN", "true").lower() == "true"


def render_login_page():
    """渲染登录页面"""
    # 添加自定义CSS样式
    st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient 3s ease infinite;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 3rem;
    }
    
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stTabs [data-baseweb="tab-list"] {
         gap: 8px;
         background-color: rgba(255,255,255,0.1);
         border-radius: 10px;
         padding: 5px;
     }
     
     .stTabs [data-baseweb="tab"] {
         background-color: transparent;
         border-radius: 8px;
         color: #333 !important;
         font-weight: 600;
         font-size: 16px !important;
     }
     
     .stTabs [aria-selected="true"] {
         background-color: rgba(255,255,255,0.8) !important;
         color: #333 !important;
     }
     
     .stTabs [data-baseweb="tab"] p {
         color: #333 !important;
         font-size: 16px !important;
         margin: 0 !important;
     }
    
    .welcome-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .feature-card {
        background: rgba(255,255,255,0.1);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 主标题
    st.markdown('<h1 class="main-title">✨ multi-agent测试平台 ✨</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">🚀 智能多代理协作平台</p>', unsafe_allow_html=True)
    
    # 欢迎卡片
    # st.markdown("""
    # <div class="welcome-card">
    #     <h2>🎯 欢迎来到未来</h2>
    #     <p>体验最先进的多代理AI协作系统，让智能助手为您的工作赋能</p>
    # </div>
    # """, unsafe_allow_html=True)
    
    # 初始化认证管理器
    if "auth_manager" not in st.session_state:
        st.session_state.auth_manager = AuthManager()
    
    auth_manager = st.session_state.auth_manager
    
    # 创建居中的容器
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 创建标签页
        tab1, tab2 = st.tabs(["🔑 登录  ", "📝 注册"])
        
        with tab1:
            # st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown("#### 🏠 登录到您的账户")
            st.markdown("欢迎回来！请输入您的凭据以继续")
            
            with st.form("login_form"):
                username = st.text_input("👤 用户名", placeholder="请输入用户名")
                password = st.text_input("🔒 密码", type="password", placeholder="请输入密码")
                
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    submit_login = st.form_submit_button("🚀 立即登录", use_container_width=True)
                
                if submit_login:
                    if username and password:
                        with st.spinner("🔄 正在验证身份..."):
                            success, message, token = auth_manager.login_user(username, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.token = token
                            st.success(f"🎉 {message}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ 请填写完整信息")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            # st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown("#### 🌟 创建新账户")
            st.markdown("加入我们的AI社区，开启智能协作之旅")
            
            with st.form("register_form"):
                new_username = st.text_input("👤 用户名", placeholder="至少3个字符，建议使用字母数字组合")
                new_email = st.text_input("📧 邮箱地址", placeholder="example@email.com")
                new_password = st.text_input("🔒 设置密码", type="password", placeholder="至少6位，包含字母和数字")
                confirm_password = st.text_input("🔐 确认密码", type="password", placeholder="再次输入密码")
                
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    submit_register = st.form_submit_button("🎯 创建账户", use_container_width=True)
                
                if submit_register:
                    if new_username and new_email and new_password and confirm_password:
                        if new_password != confirm_password:
                            st.error("❌ 两次输入的密码不一致")
                        else:
                            with st.spinner("🔄 正在创建账户..."):
                                success, message = auth_manager.register_user(new_username, new_email, new_password)
                            if success:
                                st.success(f"🎉 {message}")
                                st.balloons()
                                st.info("💡 请切换到登录标签页进行登录")
                            else:
                                st.error(f"❌ {message}")
                    else:
                        st.error("❌ 请填写完整信息")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 数据库连接状态 - 使用更窄的布局
    col_status1, col_status2, col_status3 = st.columns([1, 2, 1])
    with col_status2:
        with st.expander("🔧 系统状态"):
            if auth_manager.client:
                st.success("✅ MongoDB连接正常")
                st.info(f"📊 数据库: {auth_manager.database_name}")
                st.info(f"📁 集合: {auth_manager.collection_name}")
            else:
                st.error("❌ MongoDB连接失败")
                st.info("💡 请检查MongoDB服务是否启动")


def render_user_info():
    """渲染用户信息组件"""
    if "username" in st.session_state and "auth_manager" in st.session_state:
        auth_manager = st.session_state.auth_manager
        user_info = auth_manager.get_user_info(st.session_state.username)
        
        if user_info:
            st.sidebar.success(f"👋 欢迎, {user_info['username']}!")
            
            with st.sidebar.expander("👤 用户信息"):
                st.write(f"**用户名:** {user_info['username']}")
                st.write(f"**邮箱:** {user_info['email']}")
                if user_info.get('created_at'):
                    st.write(f"**注册时间:** {user_info['created_at'].strftime('%Y-%m-%d %H:%M')}")
                if user_info.get('last_login'):
                    st.write(f"**最后登录:** {user_info['last_login'].strftime('%Y-%m-%d %H:%M')}")
            
            if st.sidebar.button("🚪 退出登录", use_container_width=True):
                # 清除登录状态
                for key in ['logged_in', 'username', 'token']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()


def check_authentication():
    """检查用户认证状态"""
    # 如果不需要登录，直接返回True
    if not check_login_required():
        return True
    
    # 检查是否已登录
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    # 如果已登录，验证token
    if st.session_state.logged_in and "token" in st.session_state:
        if "auth_manager" not in st.session_state:
            st.session_state.auth_manager = AuthManager()
        
        auth_manager = st.session_state.auth_manager
        is_valid, username = auth_manager.verify_token(st.session_state.token)
        
        if not is_valid:
            # Token无效，清除登录状态
            st.session_state.logged_in = False
            if "token" in st.session_state:
                del st.session_state.token
            if "username" in st.session_state:
                del st.session_state.username
            st.error("🔒 登录已过期，请重新登录")
            return False
    
    return st.session_state.logged_in