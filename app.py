import streamlit as st
import streamlit.components.v1 as components
import requests
import base64
from datetime import datetime

# ==========================================
# 页面基础配置
# ==========================================
st.set_page_config(page_title="因果与功过格", page_icon="🍃")

st.markdown("""
    <style>
    .zen-header { text-align: center; color: #4a3f31; padding: 20px; border-bottom: 1px solid #eee; }
    .verse-card { background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e0e0e0; text-align: center; margin: 15px 0; color: #333 !important; }
    .gong-item { border-left: 5px solid #28a745; background: #f8fff8; padding: 10px; margin: 10px 0; border-radius: 4px; color: #111 !important; }
    .guo-item { border-left: 5px solid #dc3545; background: #fff8f8; padding: 10px; margin: 10px 0; border-radius: 4px; color: #111 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# Supabase 初始化
# ==========================================
@st.cache_resource
def get_supabase():
    """Connect to Supabase using secrets or environment variables."""
    supabase_url = st.secrets.get("supabase_url") or "https://xqatmutydxsxvrgnuwgm.supabase.co"
    supabase_key = st.secrets.get("supabase_key") or st.secrets.get("SUPABASE_KEY")
    if not supabase_key:
        st.sidebar.error("缺少 supabase_key，请检查 .streamlit/secrets.toml")
        return None
    from supabase import create_client
    return create_client(supabase_url, supabase_key)

supabase = get_supabase()

# ==========================================
# Firebase Auth (kept — separate from DB layer)
# ==========================================
WEB_KEY   = st.secrets.get("FIREBASE_WEB_API_KEY", None)
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", None)

# ==========================================
# 数据配置与 Session 状态
# ==========================================
DEFAULT_CATS = ["期权交易纪律", "研发质量把控", "女儿教育耐心", "蛋奶素食坚持", "日常布施言行"]
APP_ID = "karma_v1"

if 'user' not in st.session_state: st.session_state.user = None

KARMA_DATA = [
    {"keywords": ['投资', '股票', '期权', '交易', '财富', 'Wheel'], "question": '问今生投资顺遂、财富稳健为何因？', "verse": '无食无穿为何因。前世未舍半分文。富贵皆由命。前世各修因。', "explanation": '在金融市场中，亏损往往源于贪婪与吝啬。保持客观理性的交易纪律，获利后随分布施，是财富长流的根本。'},
    {"keywords": ['工作', '研发', '听力', '助听器', '医疗', '沟通', '测试', 'IT'], "question": '问今生能以 IT 科技与医疗设备助人为何因？', "verse": '今生健康为何因。前世施药救病人。今生聋哑为何因。前世恶口骂双亲。', "explanation": '您从事助听器测试开发，这份工作能帮助他人恢复听力，本质上就是现代版的"施药救人"。'},
    {"keywords": ['孩子', '女儿', '教育', '学习', '读书', '小学'], "question": '问今生子女乖巧、聪明好学为何因？', "verse": '聪明智慧为何因。前世诵经念佛人。多子多孙为何因。前世开笼放鸟人。', "explanation": '耐心辅导7岁女儿，能为孩子培植深厚的智慧善根。'},
    {"keywords": ['长寿', '健康', '无病', '素食', '吃素', '蛋奶素'], "question": '问今生健康长寿、坚持素食为何因？', "verse": '今生长寿为何因。前世买物多放生。今生短命是何因。前世宰杀众生身。', "explanation": '坚持蛋奶素、不食五辛，在日常生活中就是一种持续的"护生"。'}
]

FULL_TEXT_ORIGINAL = [
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

FULL_TEXT_DISPLAY = [para.replace("。", " ") for para in FULL_TEXT_ORIGINAL]

def search_karma(query):
    query = query.lower().strip()
    if not query: return None

    query_tokens = set(query.split())
    for item in KARMA_DATA:
        token_match = any(
            any(qt in kw for kw in item["keywords"])
            for qt in query_tokens
        )
        question_match = query in item["question"]
        if token_match or question_match:
            return item

    return {"question": f'关于"{query}"的参悟', "verse": "欲知前世因 今生受者是 欲知来世果 今生作者是 ", "explanation": "存善心、行善事，就是为未来种下善因。若需更深解析，可前往【大师开示】标签页请教。"}

# ==========================================
# 朗读功能 (TTS)
# ==========================================
def synthesize_speech(text, voice_preset):
    api_key = st.secrets.get("GCP_API_KEY", GEMINI_KEY)
    if not api_key: return None

    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"

    presets = {
        "温和女声": {"name": "cmn-CN-Wavenet-A", "pitch": 0.0, "rate": 0.9},
        "沉稳男声": {"name": "cmn-CN-Wavenet-B", "pitch": -2.0, "rate": 0.9},
        "清脆童声": {"name": "cmn-CN-Wavenet-D", "pitch": 6.0, "rate": 1.1}
    }
    conf = presets.get(voice_preset, presets["温和女声"])

    chunk_size = 300
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    combined_audio_bytes = b""
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, chunk in enumerate(chunks):
        status_text.text(f"大师正在诵读... ({i+1}/{len(chunks)})")
        payload = {
            "input": {"text": chunk},
            "voice": {"languageCode": "cmn-CN", "name": conf["name"]},
            "audioConfig": {"audioEncoding": "MP3", "pitch": conf["pitch"], "speakingRate": conf["rate"]}
        }
        try:
            res = requests.post(url, json=payload)
            if res.ok:
                audio_b64 = res.json().get("audioContent")
                combined_audio_bytes += base64.b64decode(audio_b64)
                progress_bar.progress((i + 1) / len(chunks))
            else:
                st.error(f"TTS API 错误 (分段 {i+1}): {res.json().get('error', {}).get('message', res.text)}")
                status_text.empty()
                progress_bar.empty()
                return None
        except Exception as e:
            st.error(f"TTS 请求异常: {e}")
            status_text.empty()
            progress_bar.empty()
            return None

    status_text.empty()
    progress_bar.empty()
    return base64.b64encode(combined_audio_bytes).decode('utf-8')


def get_cached_tts(voice_preset, full_text):
    if supabase:
        resp = supabase.table("tts_cache").select("audio_b64").eq("voice_preset", voice_preset).maybe_single().execute()
        if resp and resp.data:
            return resp.data["audio_b64"]

    st.info("首次生成该声音的音频，正在调用 Google Cloud TTS，请稍候...")
    audio_b64 = synthesize_speech(full_text, voice_preset)
    if audio_b64 and supabase:
        supabase.table("tts_cache").upsert({"voice_preset": voice_preset, "audio_b64": audio_b64}).execute()
    return audio_b64


def sanitize_prompt(text):
    """Strip control chars and length-cap user input before injection."""
    cleaned = ''.join(ch for ch in text if ord(ch) >= 32 or ch in '\n')
    return cleaned[:2000]


def call_ai_master(prompt, use_background=False):
    if not GEMINI_KEY:
        return "❌ 缺少 Gemini API 密钥配置。"
    prompt = sanitize_prompt(prompt)
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
# 认证函数 (Firebase — separate from DB)
# ==========================================
RECAPTCHA_SITE_KEY = st.secrets.get("RECAPTCHA_SITE_KEY", None)


def auth_gate(key):
    if not WEB_KEY:
        st.error("Secrets 中缺少 FIREBASE_WEB_API_KEY，无法登录。")
        return False

    if st.session_state.get("logout_message"):
        st.success(st.session_state.logout_message)
        del st.session_state["logout_message"]

    if not st.session_state.user:
        with st.container(border=True):
            st.subheader("🔑 功过格私密登录")
            mode = st.toggle("已有账号 / 注册新账号", value=False, key=f"mode_{key}")
            email = st.text_input("邮箱", key=f"e_{key}")
            pwd = st.text_input("密码", type="password", key=f"p_{key}")

            if mode and pwd and len(pwd) < 8:
                st.warning("注册密码至少需要 8 个字符。")

            if st.button("确定进入", key=f"b_{key}", type="primary"):
                if mode and len(pwd) < 8:
                    st.error("注册密码至少需要 8 个字符。")
                else:
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
    st.session_state.logout_message = "已退出登录。"

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
                <p style="font-size: 1.2em; color: #635540; font-weight: bold;">" {res["verse"]} "</p>
                <div style="color: #5c4f3c; text-align: left; margin-top: 15px; border-top: 1px solid #eee; padding-top: 15px;">
                    <b>现代启示：</b><br>{res["explanation"]}
                </div>
            </div>
        ''', unsafe_allow_html=True)

# --------- 标签 2: 功过格 ---------
with tabs[1]:
    if auth_gate("gg") and supabase:
        uid = st.session_state.user["uid"]

        # Load custom categories
        resp_cats = supabase.table("categories").select("list").eq("uid", uid).maybe_single().execute()
        user_cats = resp_cats.data["list"] if resp_cats and resp_cats.data else DEFAULT_CATS

        with st.expander("⚙️ 类别自定义"):
            new_c = st.text_input("新增类别")
            if st.button("添加类别") and new_c:
                if new_c not in user_cats:
                    user_cats.append(new_c)
                    supabase.table("categories").upsert({"uid": uid, "list": user_cats, "updated_at": datetime.now().isoformat()}).execute()
                    st.rerun()
            st.write("当前监控项：")
            st.write(", ".join(user_cats))
            if st.button("恢复默认"):
                supabase.table("categories").upsert({"uid": uid, "list": DEFAULT_CATS, "updated_at": datetime.now().isoformat()}).execute()
                st.rerun()

        st.markdown("---")
        with st.form("gg_log", clear_on_submit=True):
            c1, c2 = st.columns([3, 1])
            is_gong = c1.radio("性质", ["功 (积德)", "过 (损德)"], horizontal=True) == "功 (积德)"
            pts = c2.number_input("分值", 1, 10, 1)
            cat = st.selectbox("类别", user_cats)
            memo = st.text_area("事迹细节 (如：期权止损坚决、耐心辅导女儿)")
            if st.form_submit_button("登入功过册", type="primary"):
                supabase.table("gong_guo").insert({
                    "uid": uid, "cat": cat, "memo": memo, "pts": pts if is_gong else -pts,
                    "type": "gong" if is_gong else "guo", "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                }).execute()
                st.success("已登记")

        st.markdown("### 📜 历史记录")
        try:
            resp_recs = (
                supabase.table("gong_guo")
                .select("cat, pts, type, time, id")
                .eq("uid", uid)
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )
            records = resp_recs.data if resp_recs else []
            total = 0
            for d in records:
                cls = "gong-item" if d["type"] == "gong" else "guo-item"
                st.markdown(f'<div class="{cls}"><b>{d["cat"]} ({d["pts"]}分)</b><br><small>{d["time"]}</small><br>{d["memo"]}</div>', unsafe_allow_html=True)
                total += d["pts"]
            if records:
                st.sidebar.metric("累计功过分", total)
        except Exception as e:
            st.info(f"数据加载中，若长时间不显示请检查 Supabase 连接。错误: {e}")

    elif not supabase:
        st.warning("Supabase 未配置，无法使用功过格功能。请检查 secrets.toml。")

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
            combined_text = "".join(FULL_TEXT_ORIGINAL)
            audio_b64 = get_cached_tts(voice_choice, combined_text)

            if audio_b64:
                wrapped_text_html = ""
                for para in FULL_TEXT_DISPLAY:
                    if para.strip():
                        wrapped_text_html += "<p>"
                        for char in para:
                            display_char = "&nbsp;&nbsp;" if char == " " else char
                            wrapped_text_html += f"<span class='tts-char'>{display_char}</span>"
                        wrapped_text_html += "</p>"

                sync_html = f"""
                <style>
                    .player-wrapper {{ background: #fcfaf7; padding: 15px; border-radius: 8px; border: 1px solid #f5f0e6; margin-bottom: 20px; display: flex; flex-direction: column; gap: 10px; }}
                    .controls-row {{ display: flex; justify-content: flex-end; align-items: center; gap: 10px; }}
                    audio {{ width: 100%; outline: none; border-radius: 8px; }}
                    select {{ padding: 6px 12px; border-radius: 6px; border: 1px solid #d6cbb8; background: #fff; color: #4a3f31; font-family: 'Noto Serif SC', serif; cursor: pointer; outline: none; }}
                    .tts-text-box {{ font-family: 'Noto Serif SC', serif; font-size: 1.15rem; line-height: 2.0; color: #4a3f31; padding: 10px; word-break: break-all; }}
                    .tts-char {{ transition: color 0.1s; display: inline-block; }}
                    .highlighted {{ color: #d84315; font-weight: bold; background-color: #fbe9e7; border-radius: 2px; }}
                </style>

                <div class="player-wrapper">
                    <div class="controls-row">
                        <span style="color: #6b5c4a; font-size: 0.9rem;">实时播放速度:</span>
                        <select id="speed-selector">
                            <option value="1.0">1.0x (原速)</option>
                            <option value="1.25">1.25x (舒缓)</option>
                            <option value="1.5">1.5x (轻快)</option>
                            <option value="2.0">2.0x (极速)</option>
                        </select>
                    </div>
                    <audio id="audio-player" controls autoplay src="data:audio/mp3;base64,{audio_b64}"></audio>
                </div>

                <div class="tts-text-box" id="text-container">
                    {wrapped_text_html}
                </div>

                <script>
                    const audio = document.getElementById('audio-player');
                    const speedSelector = document.getElementById('speed-selector');
                    const spans = document.querySelectorAll('.tts-char');
                    const totalChars = spans.length;

                    speedSelector.addEventListener('change', (e) => {{
                        audio.playbackRate = parseFloat(e.target.value);
                    }});

                    audio.addEventListener('timeupdate', () => {{
                        if (audio.duration) {{
                            const progress = audio.currentTime / audio.duration;
                            const targetIndex = Math.floor(progress * totalChars);
                            spans.forEach((span, index) => {{
                                if (index <= targetIndex) {{
                                    span.classList.add('highlighted');
                                }} else {{
                                    span.classList.remove('highlighted');
                                }}
                            }});
                        }}
                    }});

                    audio.addEventListener('loadedmetadata', () => {{
                        spans.forEach(span => span.classList.remove('highlighted'));
                    }});
                </script>
                """
                components.html(sync_html, height=800, scrolling=True)
    else:
        st.markdown("---")
        for para in FULL_TEXT_DISPLAY:
            if para.strip():
                st.markdown(f"{para}  ")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #a69986; margin-top: 2rem;'>愿以此功德，普及于一切。</p>", unsafe_allow_html=True)
