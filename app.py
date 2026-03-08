import streamlit as st
import requests
import json
from datetime import datetime

# 尝试导入 firebase_admin，用于连接 Firestore 数据库
try:
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

# ==========================================
# 页面配置与禅意主题设置
# ==========================================
st.set_page_config(page_title="因果问答与功过格", page_icon="🍃", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Noto Serif SC', serif; }
    .stApp { background-color: #f9f6f0; }
    .zen-title { text-align: center; color: #4a3f31; font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem; letter-spacing: 0.1em; }
    .zen-subtitle { text-align: center; color: #6b5c4a; font-size: 1.1rem; margin-bottom: 2rem; }
    .verse-box { background-color: #ffffff; padding: 2rem; border-radius: 10px; border: 1px solid #eee8df; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 1.5rem; text-align: center; }
    .verse-text { font-size: 1.5rem; color: #635540; font-weight: bold; margin: 1rem 0; }
    .explanation-box { background-color: #fcfaf7; padding: 1.5rem; border-radius: 8px; border: 1px solid #f5f0e6; color: #5c4f3c; line-height: 1.8; }
    
    /* 功过格专用样式 */
    .gong-card { background-color: #f0f9f0; padding: 1rem 1.5rem; border-radius: 8px; border-left: 5px solid #28a745; margin-bottom: 1rem; }
    .guo-card { background-color: #fff5f5; padding: 1rem 1.5rem; border-radius: 8px; border-left: 5px solid #dc3545; margin-bottom: 1rem; }
    .score-badge { font-weight: bold; padding: 2px 8px; border-radius: 4px; font-size: 0.9rem; }
    .full-text-box { background-color: #ffffff; padding: 2.5rem; border-radius: 10px; border: 1px solid #eee8df; color: #4a3f31; line-height: 2.0; font-size: 1.1rem; }
    
    /* 类别管理小标签 */
    .category-tag {
        display: inline-block;
        background: #ede6d8;
        padding: 2px 10px;
        border-radius: 15px;
        margin: 2px;
        font-size: 0.85rem;
        color: #5c4f3c;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 环境变量与 Firebase 初始化
# ==========================================
APP_ID = "cause-n-effect" # 固定的 APP ID

@st.cache_resource
def init_firebase():
    if not FIREBASE_AVAILABLE or "firebase" not in st.secrets:
        return None
    try:
        if not firebase_admin._apps:
            cert_dict = dict(st.secrets["firebase"])
            if "\\n" in cert_dict["private_key"]:
                cert_dict["private_key"] = cert_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(cert_dict)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase 初始化失败: {e}")
        return None

db = init_firebase()

try:
    FIREBASE_WEB_API_KEY = st.secrets["FIREBASE_WEB_API_KEY"]
except:
    FIREBASE_WEB_API_KEY = None

# ==========================================
# 默认数据配置
# ==========================================
DEFAULT_CATEGORIES = [
    "交易纪律 (期权/心态)", 
    "职业操守 (技术/研发)", 
    "家庭亲情 (陪伴/耐心)", 
    "身心修持 (素食/言行)", 
    "社会公益 (布施/助人)"
]

# ==========================================
# 身份验证逻辑
# ==========================================
def sign_up_with_email(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    res = requests.post(url, json=payload)
    return res.json()

def sign_in_with_email(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    res = requests.post(url, json=payload)
    return res.json()

if 'user_uid' not in st.session_state:
    st.session_state.user_uid = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

def logout():
    st.session_state.user_uid = None
    st.session_state.user_email = None
    st.success("已退出登录。")

# ==========================================
# AI 与 静态数据
# ==========================================
KARMA_DATA = [
    {"keywords": ['投资', '股票', '期权', '交易'], "question": '问今生投资顺遂为何因？', "verse": '无食无穿为何因。前世未舍半分文。', "explanation": '守纪律即是守心。'},
    {"keywords": ['工作', '研发', '听力', '助听器'], "question": '问今生能以技术助人为何因？', "verse": '今生健康为何因。前世施药救病人。', "explanation": '利他即是利己。'}
]

def search_karma(query):
    query = query.lower().strip()
    if not query: return None
    for item in KARMA_DATA:
        if any(kw in query for kw in item['keywords']): return item
    return {"question": f"关于“{query}”的参悟", "verse": "欲知前世因。今生受者是。", "explanation": "存善心、行善事。"}

def call_ai_master(prompt, use_background=False):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception: return "❌ 缺少 API 密钥。"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    bg_info = "结合用户(46岁, 新加坡, 助听器测试开发, 期权Wheel交易, 7岁女儿, 蛋奶素)背景。" if use_background else ""
    system_instruction = f"精通《三世因果经》与《了凡四训》的智者。简体。{bg_info}结构：引用原句 + 解析。"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "systemInstruction": {"parts": [{"text": system_instruction}]}}
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        return response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "大师沉默。")
    except Exception as e: return f"❌ 错误：{str(e)}"

# ==========================================
# UI 布局
# ==========================================
st.markdown('<div class="zen-title">因果问答与功过格</div>', unsafe_allow_html=True)

if st.session_state.user_uid:
    st.markdown(f"<div style='text-align: right; color: #8a7b66;'>已登录: {st.session_state.user_email}</div>", unsafe_allow_html=True)
    if st.button("退出登录"):
        logout()
        st.rerun()
else:
    st.markdown('<div class="zen-subtitle">🍃 改过迁善，命自我立；修福积德，福自我求。</div>', unsafe_allow_html=True)

tabs = st.tabs(["💬 经典解惑", "✨ AI 大师", "📜 经文原典", "⚖️ 功过格 (了凡)"])

with tabs[0]:
    q = st.text_input("输入关键词：", placeholder="投资, 孩子...")
    if q:
        res = search_karma(q)
        st.markdown(f"<div class='verse-box'><h3>{res['question']}</h3><div class='verse-text'>“ {res['verse']} ”</div></div><div class='explanation-box'>{res['explanation']}</div>", unsafe_allow_html=True)

def require_auth(prefix):
    if not st.session_state.user_uid:
        st.warning("🔒 请先登录以使用个人云端功能。")
        with st.expander("登录 / 注册"):
            mode = st.radio("操作", ["登录", "注册"], horizontal=True, key=f"{prefix}_m")
            email = st.text_input("邮箱", key=f"{prefix}_e")
            pwd = st.text_input("密码", type="password", key=f"{prefix}_p")
            if st.button("确定", key=f"{prefix}_b"):
                res = sign_in_with_email(email, pwd) if mode == "登录" else sign_up_with_email(email, pwd)
                if "error" in res: st.error("操作失败，请检查账号密码。")
                else:
                    st.session_state.user_uid = res['localId']
                    st.session_state.user_email = res['email']
                    st.rerun()
        return False
    return True

with tabs[1]:
    if require_auth("ai"):
        ai_q = st.text_area("向大师请教：")
        use_bg = st.checkbox("结合我的背景", value=False)
        if st.button("解惑", type="primary"):
            ans = call_ai_master(ai_q, use_bg)
            st.markdown(f"<div class='explanation-box'>{ans}</div>", unsafe_allow_html=True)

with tabs[2]:
    st.markdown('<div class="full-text-box">欲知前世因，今生受者是。欲知来世果，今生作者是。</div>', unsafe_allow_html=True)

# ==========================================
# 功过格选项卡 (包含动态类别管理)
# ==========================================
with tabs[3]:
    if require_auth("gg"):
        if db is None: 
            st.error("无法连接数据库")
        else:
            uid = st.session_state.user_uid
            
            # --- 核心：获取或初始化用户自定义类别 ---
            user_settings_ref = db.collection("artifacts").document(APP_ID).collection("users").document(uid).collection("settings").document("categories")
            
            settings_doc = user_settings_ref.get()
            if settings_doc.exists:
                user_categories = settings_doc.to_dict().get("list", DEFAULT_CATEGORIES)
            else:
                user_categories = DEFAULT_CATEGORIES
                # 首次使用不强制写入，待修改后再写

            # --- 类别管理界面 ---
            with st.expander("⚙️ 功过类别管理"):
                st.markdown("您可以根据自己的生活重心，添加或删除记录类别。")
                
                # 展示当前类别
                cols_cat = st.columns([4, 1])
                new_cat = cols_cat[0].text_input("输入新类别名称", placeholder="例如：期权止损纪律", label_visibility="collapsed")
                if cols_cat[1].button("添加", use_container_width=True):
                    if new_cat and new_cat not in user_categories:
                        updated_list = user_categories + [new_cat]
                        user_settings_ref.set({"list": updated_list})
                        st.success(f"已添加：{new_cat}")
                        st.rerun()

                st.write("当前类别列表：")
                for cat in user_categories:
                    c1, c2 = st.columns([5, 1])
                    c1.markdown(f'<span class="category-tag">{cat}</span>', unsafe_allow_html=True)
                    if c2.button("删除", key=f"del_{cat}"):
                        updated_list = [c for c in user_categories if c != cat]
                        user_settings_ref.set({"list": updated_list})
                        st.rerun()
                
                if st.button("恢复默认设置"):
                    user_settings_ref.set({"list": DEFAULT_CATEGORIES})
                    st.rerun()

            st.markdown("### ✍️ 今日功过登记")
            with st.form("gg_form", clear_on_submit=True):
                col_t, col_s = st.columns([3, 1])
                with col_t:
                    entry_type = st.radio("类型", ["功 (善举/积德)", "过 (过失/损德)"], horizontal=True)
                with col_s:
                    points = st.number_input("分值", min_value=1, max_value=100, value=1)
                
                # 使用动态类别列表
                category = st.selectbox("类别", user_categories)
                detail = st.text_area("事迹详述", placeholder="记录细节：如今天止损果断(+)，或辅导女儿时保持耐心(+)...")
                
                if st.form_submit_button("登入功过册"):
                    is_gong = "功" in entry_type
                    new_record = {
                        "uid": uid,
                        "type": "gong" if is_gong else "guo",
                        "category": category,
                        "content": detail,
                        "points": points if is_gong else -points,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "server_time": firestore.SERVER_TIMESTAMP
                    }
                    db.collection("artifacts").document(APP_ID).collection("public").document("data").collection("gong_guo_ge").add(new_record)
                    st.success("已记录。")

            st.markdown("---")
            st.markdown("### ⚖️ 我的功过簿")
            
            try:
                # 获取数据 (遵循 Rule 1)
                docs = db.collection("artifacts").document(APP_ID).collection("public").document("data").collection("gong_guo_ge").where("uid", "==", uid).stream()
                records = [doc.to_dict() for doc in docs]
                records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                
                if records:
                    total_score = sum(r.get('points', 0) for r in records)
                    st.metric("累计功过分", total_score, delta=f"{records[0]['points']} (最新)")
                    for r in records[:15]:
                        card_class = "gong-card" if r['type'] == "gong" else "guo-card"
                        sign = "+" if r['type'] == "gong" else ""
                        st.markdown(f"""
                        <div class="{card_class}">
                            <div style="display: flex; justify-content: space-between;">
                                <b>{r['category']}</b>
                                <span class="score-badge" style="background: {'#d4edda' if r['type']=='gong' else '#f8d7da'}">
                                    {sign}{r['points']} 分
                                </span>
                            </div>
                            <div style="font-size: 0.85rem; color: #888; margin: 4px 0;">{r['timestamp']}</div>
                            <div style="color: #444;">{r['content']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("尚无记录。")
            except Exception as e:
                st.error(f"读取失败，可能需要创建 Firebase 索引。")