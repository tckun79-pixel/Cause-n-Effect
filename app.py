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
st.set_page_config(page_title="三世因果与福田", page_icon="🍃", layout="centered")

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
    .merit-card { background-color: #ffffff; padding: 1rem 1.5rem; border-radius: 8px; border-left: 4px solid #baaa94; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .merit-meta { font-size: 0.85rem; color: #a69986; margin-bottom: 0.5rem; }
    .full-text-box { background-color: #ffffff; padding: 2.5rem; border-radius: 10px; border: 1px solid #eee8df; color: #4a3f31; line-height: 2.0; font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# Firebase 初始化与 Auth 逻辑
# ==========================================
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

# 获取 Web API Key 用于邮箱登录
try:
    FIREBASE_WEB_API_KEY = st.secrets["FIREBASE_WEB_API_KEY"]
except:
    FIREBASE_WEB_API_KEY = None

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

# 初始化 Session State
if 'user_uid' not in st.session_state:
    st.session_state.user_uid = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

def logout():
    st.session_state.user_uid = None
    st.session_state.user_email = None
    st.success("已退出登录。")

# ==========================================
# 静态数据库与 AI 逻辑
# ==========================================
KARMA_DATA = [
    {
        "keywords": ['投资', '股票', '期权', '交易', '财富', '赚钱', 'Wheel', '老虎证券', '盈透'],
        "question": '问今生投资顺遂、财富稳健为何因？',
        "verse": '无食无穿为何因。前世未舍半分文。富贵皆由命。前世各修因。',
        "explanation": '在金融市场中，亏损往往源于贪婪与吝啬。保持客观理性的交易纪律，获利后随分布施，破除对金钱的过度执念，是财富长流的根本。'
    },
    {
        "keywords": ['工作', '研发', '听力', '助听器', '医疗', '沟通', '测试', 'IT'],
        "question": '问今生能以 IT 科技与医疗设备助人为何因？',
        "verse": '今生健康为何因。前世施药救病人。今生聋哑为何因。前世恶口骂双亲。',
        "explanation": '您从事助听器测试开发，这份工作能帮助他人恢复听力，本质上就是现代版的“施药救人”。严谨把控质量，本身就是积累善业。'
    },
    {
        "keywords": ['孩子', '女儿', '教育', '学习', '读书', '小学'],
        "question": '问今生子女乖巧、聪明好学为何因？',
        "verse": '聪明智慧为何因。前世诵经念佛人。多子多孙为何因。前世开笼放鸟人。',
        "explanation": '期望女儿聪慧，父母需言传身教。在家中营造平静理性的求知氛围，耐心辅导，能为孩子培植深厚的智慧善根。'
    },
    {
        "keywords": ['长寿', '健康', '无病', '素食', '吃素', '蛋奶素'],
        "question": '问今生健康长寿、坚持素食为何因？',
        "verse": '今生长寿为何因。前世买物多放生。今生短命是何因。前世宰杀众生身。',
        "explanation": '坚持蛋奶素、不食五辛，在日常生活中就是一种持续的“护生”。不与众生结怨，自然感得健康平安的果报。'
    }
]

FULL_TEXT = [
    "尔时。阿难陀尊者。在灵山会上。一千二百五十人俱。阿难顶礼合掌。绕佛三匝。胡跪合掌。请问本师释迦牟尼佛。南阎浮提。一切众生。末法时至。多生不善。不敬三宝。不重父母。无有三纲。五伦杂乱。贫穷下贱。六根不足。终日杀生害命。富贵贫穷。亦不平等。是何果报。望世尊慈悲。愿为弟子一一解说。",
    "佛告阿难。与诸大弟子言。善哉。善哉。汝等谛听。吾当为汝等分明说之。一切世间。男女老少。贫贱富贵。受苦无穷。享福不尽。皆是前生因果之报。以何所作故。先须孝敬父母。次要敬信三宝。三要戒杀放生。四要念佛布施。能种后世福田。",
    "佛说因果偈。云。",
    "富贵皆由命。前世各修因。有人受持者。世世福禄深。",
    "善男信女听言因。听念三世因果经。三世因果非小可。佛言真语莫非轻。",
    "今生做官是何因。前世黄金装佛身。前世修来今世受。紫袍金带佛前求。",
    "黄金装佛装自己。衣盖如来盖自身。莫说做官皆容易。前世不修何处来。",
    "骑马坐轿为何因。前世修桥铺路人。穿绸穿缎为何因。前世施衣济贫人。",
    "有食有穿为何因。前世茶饭施贫人。无食无穿为何因。前世未舍半分文。",
    "高楼大厦为何因。前世施米上庵门。福禄具足为何因。前世造寺建凉亭。",
    "相貌端庄为何因。前世鲜花供佛前。聪明智慧为何因。前世诵经念佛人。",
    "娇妻妾美为何因。前世佛门结善缘。夫妻长守为何因。前世幢幡供佛前。",
    "父母双全为何因。前世敬重孤独人。无父无母为何因。前世都是打鸟人。",
    "多子多孙为何因。前世开笼放鸟人。养子不大为何因。前世皆是恨他人。",
    "今生无子为何因。前世厌恨人儿孙。今生长寿为何因。前世买物多放生。",
    "今生短命是何因。前世宰杀众生身。今生无妻为何因。前世偷奸人女妻。",
    "今生守寡为何因。前世轻贱丈夫身。今生奴婢为何因。前世忘恩负义人。",
    "今生眼明为何因。前世施油点佛灯。今生眼瞎为何因。前世多看淫书人。",
    "今生缺口为何因。前世多说是非人。今生聋哑为何因。前世恶口骂双亲。",
    "今生驼背为何因。前世讥笑拜佛人。今生曲手为何因。前世打过父母人。",
    "今生曲脚为何因。前世破坏路桥人。今生牛马为何因。前世欠债不还人。",
    "今生猪狗为何因。前世存心哄骗人。今生多病为何因。前世幸灾乐祸人。",
    "今生健康为何因。前世施药救病人。今生坐牢为何因。前世见危不救人。",
    "今生饿死为何因。前世笑骂乞丐人。被人毒死为何因。前世拦河毒鱼人。",
    "零丁孤苦为何因。前世恶心侵算人。今生矮小为何因。前世鄙视各佣人。",
    "今生吐血为何因。前世挑拨离间人。今生耳聋为何因。前世闻法不信真。",
    "今生疮癫为何因。前世虐待畜生身。身生臭气为何因。前世妒忌他人荣。",
    "今生吊死为何因。前世损人利己人。鳏寡孤独为何因。前世不爱妻儿人。",
    "雷打火烧为何因。前世毁谤修行人。虎咬蛇伤为何因。前世多结冤仇人。",
    "万般自作还自受。地狱受苦怨何人。莫道因果无人见。远在儿孙近在身。",
    "不信三宝多施舍。但看眼前受福人。前世修来今生受。今生积德后荫人。",
    "若人毁谤因果经。后世堕落失人身。有人信行因果经。福禄寿星照临门。",
    "有人推介因果经。代代吉庆家道兴。有人常带因果经。凶灾横祸不临身。",
    "有人讲说因果经。生生世世得聪明。有人读诵因果经。来生到处人恭敬。",
    "有人印送因果经。来世便得帝王身。若问前世因果事。迦叶布施获金光。",
    "若问后世因和果。善星谤法地狱因。若是因果无报应。目莲救母是何因。",
    "若人深信因果经。同生西方极乐人。三世因果说不尽。龙天不亏善心人。",
    "三宝门中福好修。一文喜舍万文收。与君寄在坚牢库。世世生生福不休。",
    "若问前生事。今生受者是。若问后世事。今生做者是。"
]

def search_karma(query):
    query = query.lower().strip()
    if not query: return None
    for item in KARMA_DATA:
        if any(kw in query for kw in item['keywords']) or query in item['question']:
            return item
    return {"question": f"关于“{query}”的参悟", "verse": "欲知前世因。今生受者是。欲知来世果。今生作者是。", "explanation": "存善心、行善事，就是为未来种下善因。若需更深解析，可前往【AI 大师】标签页请教。"}

def call_ai_master(prompt):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        return "❌ 缺少 Gemini API 密钥配置。"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    system_instruction = """精通佛教《三世因果经》的智者。严格遵守：
    1. 依据核心原理，使用简体中文。
    2. 客观中立。结合用户(新加坡, IT/助听器, 期权交易, 7岁女儿, 蛋奶素)背景理性映射。不宣扬迷信。
    3. 第一部分引用原句，第二部分给出白话解析。"""
    
    payload = {"contents": [{"parts": [{"text": prompt}]}], "systemInstruction": {"parts": [{"text": system_instruction}]}}
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        if not response.ok: return f"❌ API 拒绝: {response.status_code}"
        return response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "大师沉默。")
    except Exception as e:
        return f"❌ 网络错误：{str(e)}"

# ==========================================
# UI 布局 - 主页面
# ==========================================
st.markdown('<div class="zen-title">三世因果问答</div>', unsafe_allow_html=True)

# 登录状态栏
if st.session_state.user_uid:
    st.markdown(f"<div style='text-align: right; color: #8a7b66; font-size: 0.9rem;'>已登录: {st.session_state.user_email}</div>", unsafe_allow_html=True)
    if st.button("退出登录", size="small"):
        logout()
        st.rerun()
else:
    st.markdown('<div class="zen-subtitle">🍃 明因果，知进退；修善业，得善报。</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["💬 经典解惑", "✨ AI 大师", "📜 经文原典", "📝 个人福田日记"])

# Tab 1: 经典解惑 (免登录可用)
with tab1:
    cols = st.columns(4)
    quick_query = ""
    if cols[0].button("期权纪律"): quick_query = "投资"
    if cols[1].button("测试研发"): quick_query = "助听器"
    if cols[2].button("辅导女儿"): quick_query = "孩子"
    if cols[3].button("清净素食"): quick_query = "素食"

    user_query = st.text_input("或在此输入关键词查询因果：", value=quick_query)
    if user_query:
        res = search_karma(user_query)
        st.markdown(f"<div class='verse-box'><h3 style='color: #4a3f31;'>{res['question']}</h3><div class='verse-text'>“ {res['verse']} ”</div></div><div class='explanation-box'><b>现代启示：</b><br><br>{res['explanation']}</div>", unsafe_allow_html=True)

# 增加 key_prefix 解决组件 ID 重复问题
def require_auth(key_prefix):
    if not FIREBASE_WEB_API_KEY:
        st.error("系统未配置 FIREBASE_WEB_API_KEY，无法启用登录功能。")
        return False
    if not st.session_state.user_uid:
        st.warning("🔒 此功能需要登录后方可使用（数据将为您加密隔离）。")
        with st.expander("👉 点击此处 登录 / 注册", expanded=True):
            auth_mode = st.radio("选择操作", ["登录", "注册新账号"], horizontal=True, key=f"{key_prefix}_mode")
            auth_email = st.text_input("电子邮箱", key=f"{key_prefix}_email")
            auth_pwd = st.text_input("密码", type="password", key=f"{key_prefix}_pwd")
            if st.button("确认提交", key=f"{key_prefix}_submit"):
                if auth_mode == "注册新账号":
                    res = sign_up_with_email(auth_email, auth_pwd)
                    if "error" in res:
                        st.error(f"注册失败: {res['error'].get('message', '未知错误')}")
                    else:
                        st.success("注册成功！请切换到登录页面进行登录。")
                else:
                    res = sign_in_with_email(auth_email, auth_pwd)
                    if "error" in res:
                        st.error(f"登录失败: 邮箱或密码错误。")
                    else:
                        st.session_state.user_uid = res['localId']
                        st.session_state.user_email = res['email']
                        st.success("登录成功！")
                        st.rerun()
        return False
    return True

# Tab 2: AI 大师 (需登录)
with tab2:
    if require_auth("ai_tab"):
        st.info("💡 结合您的生活背景，向 AI 大师请教深度因果解析。")
        ai_query = st.text_area("您的困惑：", placeholder="例如：今天期权交易止损了，产生了懊恼情绪，如何用因果智慧化解？")
        if st.button("请大师解惑", type="primary"):
            if ai_query:
                with st.spinner('大师正在沉思...'):
                    ans = call_ai_master(ai_query)
                    st.markdown(f"<div class='explanation-box'><h3 style='color: #4a3f31; margin-top: 0;'>大师开示：</h3>{ans.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

# Tab 3: 经文 (免登录可用)
with tab3:
    st.markdown('<div class="full-text-box">', unsafe_allow_html=True)
    for para in FULL_TEXT:
        if para.strip():
            st.markdown(f"{para}  ") # 使用两个空格实现 Markdown 换行
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #a69986; margin-top: 2rem;'>愿以此功德，普及于一切。</p>", unsafe_allow_html=True)

# Tab 4: 福田日记 (需登录，数据隔离)
with tab4:
    if require_auth("diary_tab"):
        if db is None:
            st.error("⚠️ Firebase 数据库连接失败。")
        else:
            st.markdown("### ✍️ 记录今日善业 (仅您自己可见)")
            with st.form("merit_form", clear_on_submit=True):
                category = st.selectbox("善业类别", [
                    "慈悲护生 (如: 坚持素食、不杀生)", 
                    "财布施 (如: 捐助、期权盈利回馈)", 
                    "法布施 (如: 分享IT知识、把控质量)", 
                    "无畏施 (如: 情绪稳定、耐心陪伴女儿)",
                    "精进修持 (如: 读经、保持交易纪律)"
                ])
                action_detail = st.text_area("具体事迹", placeholder="例如：今天克制了交易时的贪念...")
                submitted = st.form_submit_button("种下福田 🍃")
                
                if submitted and action_detail.strip():
                    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    new_record = {
                        "uid": st.session_state.user_uid, # 核心绑定 UID
                        "email": st.session_state.user_email,
                        "category": category.split(" ")[0],
                        "action": action_detail,
                        "timestamp": timestamp_str,
                        "server_time": firestore.SERVER_TIMESTAMP
                    }
                    try:
                        db.collection("merit_logs").add(new_record)
                        st.success("✅ 善业已记录！")
                    except Exception as e:
                        st.error(f"写入失败: {e}")

            st.markdown("---")
            st.markdown("### 📜 我的福田记录")
            
            try:
                # 核心查询：仅拉取 uid 等于当前登录用户的记录
                docs = db.collection("merit_logs").where("uid", "==", st.session_state.user_uid).stream()
                
                records = [doc.to_dict() for doc in docs]
                # 在 Python 端按时间倒序排列
                records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                
                if not records:
                    st.info("尚未有记录，快来种下第一块福田吧！")
                else:
                    for data in records[:20]: # 仅显示最近 20 条
                        st.markdown(f"""
                        <div class="merit-card">
                            <div class="merit-meta">🏷️ {data.get('category', '')} &nbsp;|&nbsp; 🕒 {data.get('timestamp', '')}</div>
                            <div style="color: #4a3f31; font-size: 1.05rem;">{data.get('action', '')}</div>
                        </div>
                        """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"读取数据失败: {e}")