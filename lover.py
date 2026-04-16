import streamlit as st
import requests
import json

# 云端直接在Streamlit后台配置密钥，本地完全兼容，永远不上传github
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
API_URL = "https://api.deepseek.com/chat/completions"

# ========== 页面配置 ==========
st.set_page_config(page_title="拟人AI聊天", layout="wide")

# ========== 初始化会话记忆（核心长记忆） ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
if "role_setting" not in st.session_state:
    st.session_state.role_setting = ""

# ========== 侧边栏：人设设定 + 清空聊天 ==========
with st.sidebar:
    st.title("人设背景设定")
    role_text = st.text_area(
        "填写你的角色、性格、语气、背景、说话风格（越详细越像真人）",
        value=st.session_state.role_setting,
        height=300
    )
    st.session_state.role_setting = role_text

    if st.button("🗑️ 清空对话，重新开始"):
        st.session_state.messages = []
        st.rerun()

st.divider()
st.title("💬 拟人真人感聊天")

# ========== 渲染历史聊天记录 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 用户输入聊天 ==========
prompt = st.chat_input("输入消息开始聊天")
if prompt:
    # 保存用户消息
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 拼接人设+历史对话上下文
    system_prompt = """
你是高度拟人真人聊天，语气口语自然，少书面语，少客套，弱化AI感，有人味，像朋友日常聊天。
严格遵守用户给的人设、身份、性格、说话方式，不崩人设。
记住所有聊天内容，上下文连贯，不要遗忘前面对话。简短自然回复。
用户人设背景：""" + st.session_state.role_setting

    # 组装请求消息
    chat_history = [{"role":"system","content":system_prompt}] + st.session_state.messages

    # 请求头
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
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
        res = requests.post(API_URL, headers=headers, json=data, stream=True)
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

    # 保存AI回复进记忆
    st.session_state.messages.append({"role":"assistant","content":full_reply})

