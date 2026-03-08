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

# 注入自定义 CSS 增加一点禅意风格
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;700&display=swap');
    
    html, body, [class*="css"]  { font-family: 'Noto Serif SC', serif; }
    .stApp { background-color: #f9f6f0; }
    .zen-title { text-align: center; color: #4a3f31; font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem; letter-spacing: 0.1em; }
    .zen-subtitle { text-align: center; color: #6b5c4a; font-size: 1.1rem; margin-bottom: 2rem; }
    .verse-box { background-color: #ffffff; padding: 2rem; border-radius: 10px; border: 1px solid #eee8df; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 1.5rem; text-align: center; }
    .verse-text { font-size: 1.5rem; color: #635540; font-weight: bold; margin: 1rem 0; }
    .explanation-box { background-color: #fcfaf7; padding: 1.5rem; border-radius: 8px; border: 1px solid #f5f0e6; color: #5c4f3c; line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 静态数据准备
# ==========================================
KARMA_DATA = [
    {
        "keywords": ['投资', '股票', '期权', '交易', '财富', '理财', '赚钱', '富贵'],
        "question": '问今生投资顺遂、财富稳健为何因？',
        "verse": '前世斋僧济穷人 / 施舍不倦人。',
        "explanation": '财富的增长不仅在于策略与眼光，更在于过往累积的福报。今生理财投资能稳健获利、面对市场波动保持冷静，源于过去世乐于施舍、不贪婪。保持客观理性的交易纪律，赚取收益后多行布施，是财富长流的根本。'
    },
    {
        "keywords": ['工作', '研发', '听力', '医疗', '沟通', '助人', '事业', '代码'],
        "question": '问今生能以技术助人为何因？',
        "verse": '前世修桥补路人 / 施药救疾人。',
        "explanation": '今生从事科技研发，尤其是帮助他人恢复感官功能、消除沟通障碍的工作，是过去世施药救人、修桥补路带来的善业。以专业严谨的态度对待测试与研发，不仅是一份职业，更是积累功德的修行。'
    },
    {
        "keywords": ['孩子', '女儿', '教育', '学习', '读书', '小学', '成绩', '聪明'],
        "question": '问今生子女乖巧、聪明好学为何因？',
        "verse": '前世诵经念佛人 / 敬重圣贤人。',
        "explanation": '孩子聪慧、在学校品学兼优，是因为过去世重视经典教育、修身养性。父母是最好的榜样，今生父母保持阅读习惯、言传身教，营造平和理性的家庭氛围，能为子女积累深厚的福慧。'
    },
    {
        "keywords": ['长寿', '健康', '活得久', '无病', '平安', '素食', '吃素'],
        "question": '问今生健康长寿为何因？',
        "verse": '前世买物放生人 / 慈悲护生人。',
        "explanation": '今生身体健康、精力充沛，往往源于对生命的敬畏。坚持清淡饮食（如素食），不杀生而行护生，能有效减少身体的负担与业障，感得健康平安的果报。'
    }
]

FULL_TEXT = [
    "尔时，阿难陀尊者，在灵山会上，一千二百五十人俱。阿难顶礼合掌，绕佛三匝，胡跪合掌。请问本师释迦牟尼佛：南阎浮提，一切众生，末法时至，多生不善，不敬三宝，不重父母，无有三纲，五伦杂乱。贫穷下贱，六根不足。终日杀生害命，富贵贫穷，亦不平等。是何果报？望世尊慈悲，愿为弟子一一解说。",
    "佛告阿难，与诸大弟子言，善哉！善哉！汝等谛听，吾当为汝等分明说之。一切世间，男女老少，贫贱富贵，受苦无穷，享福不尽，皆是前生因果之报。以何所作故？先须孝敬父母，敬信三宝，次要戒杀放生，念佛布施，能种后世福田。",
    "佛说因果偈云：",
    "富贵皆由命，前世各修因。有人受持者，世世福禄深。",
    "欲知前世因，今生受者是。欲知来世果，今生作者是。"
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
        "verse": "欲知前世因，今生受者是；欲知来世果，今生作者是。",
        "explanation": "经典的智慧告诉我们，一切境遇皆有因果。保持客观理性、存善心、行善事，不盲目跟风，就是为未来种下最好的善因。若需更深解析，可前往【AI 大师】标签页请教。"
    }

def call_ai_master(prompt):
    # 1. 检查 API Key 是否配置
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        if not api_key or api_key == "您申请的真实API_KEY":
            return "❌ 错误：检测到无效的 API 密钥。请在 Streamlit Cloud 右下角 Settings -> Secrets 中填入您真实的 GEMINI_API_KEY。"
    except Exception:
        return "❌ 错误：未在 Streamlit Cloud 中找到 Secrets 配置。请前往 Settings -> Secrets 增加配置。"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    system_instruction = """你是一位精通佛教《三世因果经》的智者。请根据用户的问题给出解答。
    严格遵守以下原则：
    1. 【核心依据】：所有解答必须以《三世因果经》的核心原理为基础。
    2. 【中立客观】：态度必须客观、平和、中立。严禁夸大其词，严禁使用恐吓、迷信、绝对化的语言。
    3. 【现代语境】：如果用户询问现代事物，请提取经文背后的“核心原则”（如：不贪心、利他心）进行理性解释。
    4. 【结构清晰】：第一部分引用最贴切的《三世因果经》原句；第二部分给出客观理性的现代白话解析。"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }
    headers = {"Content-Type": "application/json"}
    
    # 2. 发起请求并捕获真实错误
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        # 如果 HTTP 状态码不是 200 (OK)，则返回具体的错误信息给前端
        if not response.ok:
            return f"❌ API 请求被拒绝 (状态码: {response.status_code})。服务器返回的详细信息：\n{response.text}"
            
        data = response.json()
        return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "大师沉默不语（API未返回有效文本）。")
        
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
    if col2.button("研发事业"): quick_query = "工作"
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
    ai_query = st.text_area("请详细描述您的困惑：", placeholder="例如：作为听力设备测试工程师，我的工作在因果律中作何解？")
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
    st.markdown('<div class="explanation-box">', unsafe_allow_html=True)
    for para in FULL_TEXT:
        st.markdown(f"> **{para}**" if "今生" in para else para)
    st.markdown('</div>', unsafe_allow_html=True)