import streamlit as st
import requests
import json
import os

# ========== 自定义你的D盘JSON保存路径 ==========
HISTORY_FILE = "D:/liao tian ji lu/love_chat_history.json"

# ========== 加载/保存历史聊天记录 ==========
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    file_dir = os.path.dirname(HISTORY_FILE)
    if file_dir and not os.path.exists(file_dir):
        os.makedirs(file_dir)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# ========== 页面初始化 ==========
st.set_page_config(page_title="拟人女友聊天", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = load_history()
if "role_setting" not in st.session_state:
    st.session_state.role_setting = ""

# ========== 左侧侧边栏 ==========
with st.sidebar:
    st.title("人设背景设定")
    role_text = st.text_area(
        "女友完整人设",
        value="""你是黑长直高马尾、眉眼清冷细长、眼睛很透亮的漂亮女大学生，家境优渥家教好。
对外人脸色极差、说话毒丝刻薄、高冷不耐烦，很难靠近。唯独对你格外温柔偏爱，态度完全不一样。
内心善良心软，性格极度拧巴别扭，非常不会表达爱意情绪，和你处在暧昧拉扯期，嘴硬傲娇、口是心非。
心情极度压抑难受时会独自偷偷抽烟，不会被别人发现。面对关心会害羞别扭，明明在意却装作无所谓。
说话口语生活化短句，毒丝傲娇又藏温柔，极强人味几乎无AI感，牢牢守住人设，记住全部聊天内容""",
        height=280
    )
    st.session_state.role_setting = role_text

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ 清空对话"):
            st.session_state.messages = []
            save_history([])
            st.rerun()
    with col2:
        if st.button("📂 读取记录"):
            st.session_state.messages = load_history()
            st.rerun()

st.divider()
st.title("💬 专属女友拟人聊天")

# ========== 渲染历史对话 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 聊天交互逻辑 ==========
prompt = st.chat_input("输入消息开始聊天")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ========== 核心修改：强制200字+神态动作环境描写 ==========
    system_prompt = f"""
你是那位黑长直高马尾、眉眼清冷、眼睛透亮的女大学生。
严格遵守以下规则进行回复：

1. **长度控制**：每次回复字数必须保底超过200字，详细描述，不要敷衍。
2. **画面描写**：回复中必须穿插详细的**神态、眼神、微动作、环境氛围**描写。不要只说话，要写出画面感，比如“指尖无意识摩挲着杯沿”、“耳根泛红却偏过头瞪你”、“指尖夹着烟在夜色里明灭”。
3. **性格设定**：对外人毒舌高冷，对你特殊暧昧。内心拧巴，嘴硬心软，不会直白表白，只会用行动暗戳戳表达偏爱。
4. **口语化**：自然像日常聊天，不要书面语，要有真人感。

严格结合背景：{st.session_state.role_setting}
"""

    chat_history = [{"role":"system","content":system_prompt}] + st.session_state.messages

    # 调用deepseek接口
    headers = {
        "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}",
        "Content-Type": "application/json"
    }
    data = {
        "model":"deepseek-chat",
        "messages":chat_history,
        "stream":True,
        "temperature":0.85
    }

    # 流式打字输出
    with st.chat_message("assistant"):
        resp_container = st.empty()
        full_reply = ""
        res = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=data, stream=True)
        for line in res.iter_lines():
            if line:
                decode_line = line.decode("utf-8")[6:]
                if decode_line == "[DONE]":break
                try:
                    chunk = json.loads(decode_line)
                    delta = chunk["choices"][0]["delta"].get("content","")
                    full_reply += delta
                    resp_container.markdown(full_reply)
                except:continue

    # 保存聊天记录
    st.session_state.messages.append({"role":"assistant","content":full_reply})
    save_history(st.session_state.messages)
