import streamlit as st
import requests
import json
import base64
from datetime import datetime

# 1. 尝试导入并检查依赖
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_READY = True
except ImportError:
    FIREBASE_READY = False

# ==========================================
# 页面基础配置 (不再强制覆盖全局背景颜色)
# ==========================================
st.set_page_config(page_title="因果与功过格", page_icon="🍃")

# 局部样式注入：仅针对特定卡片，不干扰全局文字颜色
st.markdown("""
    <style>
    .zen-header { text-align: center; color: #4a3f31; padding: 20px; border-bottom: 1px solid #eee; }
    .verse-card { background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e0e0e0; text-align: center; margin: 15px 0; color: #333 !important; }
    .gong-item { border-left: 5px solid #28a745; background: #f8fff8; padding: 10px; margin: 10px 0; border-radius: 4px; color: #111 !important; }
    .guo-item { border-left: 5px solid #dc3545; background: #fff8f8; padding: 10px; margin: 10px 0; border-radius: 4px; color: #111 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 核心初始化与安全检查
# ==========================================
@st.cache_resource
def get_db():
    if not FIREBASE_READY or "firebase" not in st.secrets:
        return None
    try:
        if not firebase_admin._apps:
            fb_conf = dict(st.secrets["firebase"])
            fb_conf["private_key"] = fb_conf["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(fb_conf)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.sidebar.error(f"DB初始化异常: {e}")
        return None

db = get_db()

# 获取 Auth 必要的 Web Key
WEB_KEY = st.secrets.get("FIREBASE_WEB_API_KEY", None)
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", None)

# ==========================================
# 数据配置与 Session 状态
# ==========================================
DEFAULT_CATS = ["期权交易纪律", "研发质量把控", "女儿教育耐心", "蛋奶素食坚持", "日常布施言行"]
APP_ID = "karma_v1"

if 'user' not in st.session_state: st.session_state.user = None

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
    return {"question": f"关于“{query}”的参悟", "verse": "欲知前世因。今生受者是。欲知来世果。今生作者是。", "explanation": "存善心、行善事，就是为未来种下善因。若需更深解析，可前往【大师开示】标签页请教。"}

def call_ai_master(prompt, use_background=False):
    if not GEMINI_KEY:
        return "❌ 缺少 Gemini API 密钥配置。"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
    
    bg_instruction = "结合用户(新加坡, IT/助听器, 期权交易, 7岁女儿, 蛋奶素)等背景进行理性映射。" if use_background else "仅针对用户当前的问题进行客观解答，不要生搬硬套任何未经提及的个人背景。"
    
    system_instruction = f"""精通佛教《三世因果经》的智者。严格遵守：
    1. 依据核心原理，使用简体中文。
    2. 客观中立。{bg_instruction}不宣扬迷信。
    3. 第一部分引用原句，第二部分给出白话解析。"""
    
    payload = {"contents": [{"parts": [{"text": prompt}]}], "systemInstruction": {"parts": [{"text": system_instruction}]}}
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        if not response.ok: return f"❌ API 拒绝: {response.status_code}"
        return response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "大师沉默。")
    except Exception as e:
        return f"❌ 网络错误：{str(e)}"

# ==========================================
# 朗读功能 (TTS)
# ==========================================
def synthesize_speech(text, voice_preset):
    # 优先使用专门的 GCP_API_KEY，如果没有则尝试复用 GEMINI_KEY
    api_key = st.secrets.get("GCP_API_KEY", GEMINI_KEY)
    if not api_key: return None

    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"

    presets = {
        "温和女声": {"name": "cmn-CN-Wavenet-A", "pitch": 0.0, "rate": 0.9},
        "沉稳男声": {"name": "cmn-CN-Wavenet-B", "pitch": -2.0, "rate": 0.9},
        "清脆童声": {"name": "cmn-CN-Wavenet-D", "pitch": 6.0, "rate": 1.1}
    }
    conf = presets.get(voice_preset, presets["温和女声"])

    payload = {
        "input": {"text": text},
        "voice": {"languageCode": "cmn-CN", "name": conf["name"]},
        "audioConfig": {"audioEncoding": "MP3", "pitch": conf["pitch"], "speakingRate": conf["rate"]}
    }

    try:
        res = requests.post(url, json=payload)
        if res.ok:
            return res.json().get("audioContent")
        else:
            st.error(f"TTS API 错误: {res.json().get('error', {}).get('message', res.text)}")
            return None
    except Exception as e:
        st.error(f"TTS 请求异常: {e}")
        return None

def get_cached_tts(voice_preset, full_text):
    if not db: 
        return synthesize_speech(full_text, voice_preset)
        
    cache_ref = db.collection("artifacts").document(APP_ID).collection("public").document("data").collection("tts_cache").document(voice_preset)
    doc = cache_ref.get()
    if doc.exists:
        return doc.to_dict().get("audio_b64")

    st.info("首次生成该声音的音频，正在调用 Google Cloud TTS，请稍候...")
    audio_b64 = synthesize_speech(full_text, voice_preset)
    if audio_b64:
        try:
            cache_ref.set({"audio_b64": audio_b64, "timestamp": firestore.SERVER_TIMESTAMP})
        except:
            pass
    return audio_b64

# ==========================================
# 认证函数
# ==========================================
def auth_gate(key):
    if not WEB_KEY:
        st.error("Secrets 中缺少 FIREBASE_WEB_API_KEY，无法登录。")
        return False
    
    if not st.session_state.user:
        with st.container(border=True):
            st.subheader("🔑 功过格私密登录")
            mode = st.toggle("已有账号 / 注册新账号", value=False, key=f"mode_{key}")
            email = st.text_input("邮箱", key=f"e_{key}")
            pwd = st.text_input("密码", type="password", key=f"p_{key}")
            
            if st.button("确定进入", key=f"b_{key}", type="primary"):
                action = "signUp" if mode else "signInWithPassword"
                url = f"https://identitytoolkit.googleapis.com/v1/accounts:{action}?key={WEB_KEY}"
                try:
                    res = requests.post(url, json={"email": email, "password": pwd, "returnSecureToken": True})
                    data = res.json()
                    if "localId" in data:
                        st.session_state.user = {"uid": data["localId"], "email": data["email"]}
                        st.rerun()
                    else:
                        st.error(f"失败: {data.get('error', {}).get('message')}")
                except Exception as e:
                    st.error(f"连接异常: {e}")
        return False
    return True

def logout():
    st.session_state.user = None
    st.success("已退出登录。")

# ==========================================
# UI 渲染
# ==========================================
st.markdown('<h1 class="zen-header">三世因果与功过格</h1>', unsafe_allow_html=True)

if st.session_state.user:
    st.markdown(f"<div style='text-align: right; color: #8a7b66; font-size: 0.9rem;'>已登录: {st.session_state.user['email']}</div>", unsafe_allow_html=True)
    if st.button("退出登录"):
        logout()
        st.rerun()

tabs = st.tabs(["💬 问因果", "⚖️ 功过格", "✨ 大师开示", "📜 经文"])

# --------- 标签 1: 问因果 ---------
with tabs[0]:
    st.write("输入您在期权交易、研发或生活中的困惑关键词：")
    cols = st.columns(4)
    quick_query = ""
    if cols[0].button("期权纪律"): quick_query = "投资"
    if cols[1].button("测试研发"): quick_query = "助听器"
    if cols[2].button("辅导女儿"): quick_query = "孩子"
    if cols[3].button("清净素食"): quick_query = "素食"

    q = st.text_input("关键词查询", value=quick_query, placeholder="如：投资、健康、孩子", label_visibility="collapsed")
    if q:
        res = search_karma(q)
        st.markdown(f'''
            <div class="verse-card">
                <h4 style="color:#4a3f31;">{res["question"]}</h4>
                <p style="font-size: 1.2em; color: #635540; font-weight: bold;">“ {res["verse"]} ”</p>
                <div style="color: #5c4f3c; text-align: left; margin-top: 15px; border-top: 1px solid #eee; padding-top: 15px;">
                    <b>现代启示：</b><br>{res["explanation"]}
                </div>
            </div>
        ''', unsafe_allow_html=True)

# --------- 标签 2: 功过格 ---------
with tabs[1]:
    if auth_gate("gg"):
        uid = st.session_state.user["uid"]
        
        # 1. 获取类别设置
        settings_ref = db.collection("artifacts").document(APP_ID).collection("users").document(uid).collection("settings").document("categories")
        doc = settings_ref.get()
        user_cats = doc.to_dict().get("list", DEFAULT_CATS) if doc.exists else DEFAULT_CATS
        
        # 2. 类别管理
        with st.expander("⚙️ 类别自定义"):
            new_c = st.text_input("新增类别")
            if st.button("添加类别") and new_c:
                if new_c not in user_cats:
                    user_cats.append(new_c)
                    settings_ref.set({"list": user_cats})
                    st.rerun()
            st.write("当前监控项：")
            st.write(", ".join(user_cats))
            if st.button("恢复默认"):
                settings_ref.set({"list": DEFAULT_CATS})
                st.rerun()

        # 3. 记录
        st.markdown("---")
        with st.form("gg_log", clear_on_submit=True):
            c1, c2 = st.columns([3, 1])
            is_gong = c1.radio("性质", ["功 (积德)", "过 (损德)"], horizontal=True) == "功 (积德)"
            pts = c2.number_input("分值", 1, 10, 1)
            cat = st.selectbox("类别", user_cats)
            memo = st.text_area("事迹细节 (如：期权止损坚决、耐心辅导女儿)")
            if st.form_submit_button("登入功过册", type="primary"):
                db.collection("artifacts").document(APP_ID).collection("public").document("data").collection("gong_guo").add({
                    "uid": uid, "cat": cat, "memo": memo, "pts": pts if is_gong else -pts,
                    "type": "gong" if is_gong else "guo", "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "server_time": firestore.SERVER_TIMESTAMP
                })
                st.success("已登记")

        # 4. 展示
        st.markdown("### 📜 历史记录")
        try:
            recs = db.collection("artifacts").document(APP_ID).collection("public").document("data").collection("gong_guo").where("uid", "==", uid).order_by("server_time", direction=firestore.Query.DESCENDING).limit(10).stream()
            total = 0
            for r in recs:
                d = r.to_dict()
                cls = "gong-item" if d["type"] == "gong" else "guo-item"
                st.markdown(f'<div class="{cls}"><b>{d["cat"]} ({d["pts"]}分)</b><br><small>{d["time"]}</small><br>{d["memo"]}</div>', unsafe_allow_html=True)
                total += d["pts"]
            st.sidebar.metric("累计功过分", total)
        except:
            st.info("数据加载中，若长时间不显示请检查 Firebase 索引。")

# --------- 标签 3: 大师开示 ---------
with tabs[2]:
    if auth_gate("ai"):
        st.info("💡 向 AI 大师请教深度因果解析。")
        ai_q = st.text_area("您的困惑：", placeholder="例如：遇到了挫折，产生了懊恼情绪，如何用因果智慧化解？")
        use_bg = st.checkbox("结合我的生活背景 (新加坡、IT、期权、女儿等)", value=False)
        if st.button("请大师解惑", type="primary"):
            if ai_q:
                with st.spinner('大师正在沉思...'):
                    ans = call_ai_master(ai_q, use_background=use_bg)
                    st.markdown(f"<div class='verse-card' style='text-align: left;'><b>大师开示：</b><br><br>{ans.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

# --------- 标签 4: 经文 ---------
with tabs[3]:
    st.markdown('<div class="verse-card" style="text-align: left; line-height: 2.0; font-size: 1.1rem;">', unsafe_allow_html=True)
    
    st.markdown("### 🎧 聆听经文")
    col1, col2 = st.columns([2, 1])
    voice_choice = col1.selectbox("选择朗读声音", ["温和女声", "沉稳男声", "清脆童声"], label_visibility="collapsed")
    if col2.button("加载/播放朗读"):
        if not st.secrets.get("GCP_API_KEY") and not GEMINI_KEY:
            st.error("请在 Secrets 中配置 API_KEY 以启用朗读功能。")
        else:
            combined_text = "".join(FULL_TEXT)
            audio_b64 = get_cached_tts(voice_choice, combined_text)
            if audio_b64:
                audio_bytes = base64.b64decode(audio_b64)
                st.audio(audio_bytes, format="audio/mp3")
    
    st.markdown("---")

    for para in FULL_TEXT:
        if para.strip():
            st.markdown(f"{para}  ")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #a69986; margin-top: 2rem;'>愿以此功德，普及于一切。</p>", unsafe_allow_html=True)