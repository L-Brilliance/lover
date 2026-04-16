import streamlit as st
import requests
import json
import os
from datetime import datetime

# ========== 这里自由自定义JSON保存路径！！！ ==========
# 桌面路径示例：HISTORY_FILE = "C:/Users/你的名字/Desktop/聊天记录.json"
HISTORY_FILE = "D:/liao tian ji lu/love_chat_history.json"

# ========== 加载历史记录 ==========
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    # 自动创建上级文件夹，路径不存在也不会报错
    file_dir = os.path.dirname(HISTORY_FILE)
    if file_dir and not os.path.exists(file_dir):
        os.makedirs(file_dir)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# ========== 页面配置 ==========
st.set_page_config(page_title="拟人AI聊天", layout="wide")

# ========== 初始化会话 ==========
if "messages" not in st.session_state:
    st.session_state.messages = load_history()
if "role_setting" not in st.session_state:
    st.session_state.role_setting = ""

# ========== 侧边栏 ==========
with st.sidebar:
    st.title("人设背景设定")
    role_text = st.text_area(
        "填写你的角色、性格、语气、背景、说话风格（越详细越像真人）",
        value=st.session_state.role_setting,
        height=300
    )
    st.session_state.role_setting = role_text

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ 清空对话"):
            st.session_state.messages = []
            save_history([])
            st.rerun()
    with col2:
        if st.button("📂 重新读取记录"):
            st.session_state.messages = load_history()
            st.rerun()

st.divider()
st.title("💬 拟人真人感聊天")

# ========== 渲染历史对话 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 聊天交互 ==========
prompt = st.chat_input("输入消息开始聊天")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 人设prompt
    system_prompt = """
你是高度拟人真人聊天，语气口语自然，少书面语，少客套，弱化AI感，有人味，像朋友日常聊天。
严格遵守用户给的人设、身份、性格、说话方式，不崩人设。
记住所有聊天内容，上下文连贯，不要遗忘前面对话。简短自然回复。
用户人设背景：""" + st.session_state.role_setting

    chat_history = [{"role":"system","content":system_prompt}] + st.session_state.messages

    # 调用deepseek
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

    # 保存记录写入本地JSON
    st.session_state.messages.append({"role":"assistant","content":full_reply})
    save_history(st.session_state.messages)
