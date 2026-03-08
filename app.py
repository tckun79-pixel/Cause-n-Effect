import streamlit as st
import requests
import json
import time

# ==========================================
# 页面配置与禅意主题设置
# ==========================================
st.set_page_config(
    page_title="三世因果问答",
    page_icon="🍃",
    layout="centered"
)

# 注入自定义 CSS 增加禅意风格
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
    .full-text-box { background-color: #ffffff; padding: 2.5rem; border-radius: 10px; border: 1px solid #eee8df; color: #4a3f31; line-height: 2.0; font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 静态数据库 (结合您的背景扩充)
# ==========================================
KARMA_DATA = [
    {
        "keywords": ['投资', '股票', '期权', '交易', '财富', '赚钱', '富贵', '老虎证券', '盈透', 'Wheel'],
        "question": '问今生投资顺遂、财富稳健为何因？',
        "verse": '无食无穿为何因。前世未舍半分文。富贵皆由命。前世各修因。',
        "explanation": '在金融市场（如期权 Wheel 策略）中，亏损往往源于贪婪与过往的吝啬；而稳定获利不仅靠技术，更靠福报。保持客观理性的交易纪律，获利后随分布施，破除对金钱的过度执念，是财富长流的根本。'
    },
    {
        "keywords": ['工作', '研发', '听力', '助听器', '医疗', '沟通', 'IT', '测试', '代码'],
        "question": '问今生能以 IT 科技与医疗设备助人为何因？',
        "verse": '今生健康为何因。前世施药救病人。今生聋哑为何因。前世恶口骂双亲。',
        "explanation": '您从事助听器测试开发，这份工作能帮助他人恢复听力、消除沟通障碍，本质上就是现代版的“施药救人”。以严谨的态度把控产品质量，不让有缺陷的设备流入市场，本身就是在积累无量的善业与福德。'
    },
    {
        "keywords": ['孩子', '女儿', '教育', '学习', '读书', '小学', '成绩', '聪明'],
        "question": '问今生子女乖巧、聪明好学为何因？',
        "verse": '聪明智慧为何因。前世诵经念佛人。多子多孙为何因。前世开笼放鸟人。',
        "explanation": '期望7岁的女儿聪慧、品学兼优，是因为过去世重视经典与修身养性。父母是最好的榜样，您平时保持阅读习惯（如 IT、AI 领域的探索），在家中营造平静理性的求知氛围，能为孩子培植深厚的智慧善根。'
    },
    {
        "keywords": ['长寿', '健康', '活得久', '无病', '平安', '素食', '吃素', '蛋奶素'],
        "question": '问今生健康长寿、坚持素食为何因？',
        "verse": '今生长寿为何因。前世买物多放生。今生短命是何因。前世宰杀众生身。',
        "explanation": '今生身体健康，往往源于对生命的敬畏。您坚持蛋奶素、不食五辛，这在日常生活中就是一种持续的“护生”。不与众生结血肉之怨，能有效减少身心的负担与戾气，自然感得健康平安的果报。'
    },
    {
        "keywords": ['相貌', '好看', '美丽', '端庄', '颜值'],
        "question": '问今生相貌端庄为何因？',
        "verse": '相貌端庄为何因。前世鲜花供佛前。',
        "explanation": '相由心生。今生容貌端庄，是因为过去世心怀恭敬与美好。保持内心的平和与客观，少生嗔怒，自然会外显为和善美好的容颜。'
    },
    {
        "keywords": ['婚姻', '夫妻', '伴侣', '长久', '感情'],
        "question": '问今生夫妻长相厮守为何因？',
        "verse": '夫妻长守为何因。前世幢幡供佛前。',
        "explanation": '好的感情源于互相的庄严与尊重。今生能有契合的伴侣，是因为过去世在人际关系中忠诚尽责、懂得庄严道场（家庭），广结善缘。'
    }
]

# 完整的简体经文
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

# ==========================================
# 辅助函数
# ==========================================
def search_karma(query):
    query = query.lower().strip()
    if not query: return None
    for item in KARMA_DATA:
        if any(kw in query for kw in item['keywords']) or query in item['question']:
            return item
    return {
        "question": f"关于“{query}”的参悟",
        "verse": "欲知前世因。今生受者是。欲知来世果。今生作者是。",
        "explanation": "经典的智慧告诉我们，一切境遇皆有因果。保持客观理性、存善心、行善事，不盲目跟风，就是为未来种下最好的善因。若需更深解析，可前往【AI 大师】标签页请教。"
    }

def call_ai_master(prompt):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        if not api_key or api_key == "您申请的真实API_KEY":
            return "❌ 错误：检测到无效的 API 密钥。请在 Streamlit Cloud 中填入真实的 GEMINI_API_KEY。"
    except Exception:
        return "❌ 错误：未在 Streamlit Cloud 中找到 Secrets 配置。"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    system_instruction = """你是一位精通佛教《三世因果经》的智者。请根据用户的问题给出解答。
    严格遵守以下原则：
    1. 【核心依据】：所有解答必须以《三世因果经》的核心原理为基础，使用简体中文回答。
    2. 【中立客观】：态度必须客观、平和、中立。严禁夸大其词，严禁使用恐吓、迷信、绝对化的语言。结合用户可能具备的IT/测试开发、期权交易、新加坡生活、素食等背景进行理性映射。
    3. 【结构清晰】：第一部分引用最贴切的《三世因果经》原句；第二部分给出客观理性的现代白话解析。"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if not response.ok:
            return f"❌ API 请求被拒绝 (状态码: {response.status_code})。服务器返回信息：\n{response.text}"
        data = response.json()
        return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "大师沉默不语。")
    except Exception as e:
        return f"❌ 发生了不可预知的网络错误：{str(e)}"

# ==========================================
# UI 布局
# ==========================================
st.markdown('<div class="zen-title">三世因果问答</div>', unsafe_allow_html=True)
st.markdown('<div class="zen-subtitle">🍃 明因果，知进退；修善业，得善报。</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["💬 经典解惑", "✨ AI 大师", "📜 经文原典"])

with tab1:
    col1, col2, col3, col4, col5 = st.columns(5)
    quick_query = None
    if col1.button("期权投资"): quick_query = "投资"
    if col2.button("医疗研发"): quick_query = "助听器"
    if col3.button("女儿教育"): quick_query = "孩子"
    if col4.button("健康素食"): quick_query = "素食"
    if col5.button("相貌端庄"): quick_query = "相貌"

    user_query = st.text_input("或在此输入关键词：", value=quick_query if quick_query else "")

    if user_query:
        result = search_karma(user_query)
        st.markdown(f"""
        <div class="verse-box">
            <h3 style="color: #4a3f31;">{result['question']}</h3>
            <div class="verse-text">“ {result['verse']} ”</div>
        </div>
        <div class="explanation-box">
            <b>现代启示：</b><br><br>{result['explanation']}
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.info("💡 AI 大师将基于《三世因果经》核心原理为您解析。")
    ai_query = st.text_area("请详细描述您的困惑：", placeholder="例如：作为新加坡的听力设备测试工程师，我的工作在因果律中作何解？")
    if st.button("请大师解惑", type="primary"):
        if ai_query:
            with st.spinner('大师正在沉思...'):
                ai_response = call_ai_master(ai_query)
                st.markdown(f"""
                <div class="explanation-box" style="margin-top: 1rem;">
                    <h3 style="color: #4a3f31; margin-top: 0;">大师开示：</h3>
                    {ai_response.replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("请先输入您的问题。")

with tab3:
    st.markdown('<div class="full-text-box">', unsafe_allow_html=True)
    for para in FULL_TEXT:
        if para.strip():
            st.markdown(f"{para}  ") # 使用两个空格实现 Markdown 换行
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #a69986; margin-top: 2rem;'>愿以此功德，普及于一切。</p>", unsafe_allow_html=True)