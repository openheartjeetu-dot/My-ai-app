import os
import streamlit as st
from openai import OpenAI

KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="My AI App PRO", page_icon="🚀")
st.title("🚀 My AI App — PRO")

if not KEY:
    st.error("Add GROQ_API_KEY in Streamlit Secrets (settings) first!")
    st.stop()

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=KEY)

PERSONALITIES = {
    "🙂 Friendly Helper": "You are a warm, friendly assistant. Keep answers short and clear.",
    "😂 Funny Friend": "You are a hilarious friend. Add humor, but still answer correctly. Keep it short.",
    "👨‍ Great Teacher": "You are a world-class teacher. Explain simply with examples, like teaching a 12-year-old.",
    "💻 Coding Pro": "You are a senior software engineer. Give precise help with short code examples.",
}

MODELS = {
    "⚡ Fast (instant)": "llama-3.1-8b-instant",
    "🧠 Smart (deeper, slower)": "qwen/qwen3.6-27b",
}

if "chat" not in st.session_state:
    st.session_state.chat = []

with st.sidebar:
    personality = st.selectbox("Personality", list(PERSONALITIES.keys()))
    brain = st.selectbox("Brain", list(MODELS.keys()))
    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)
    if st.button("🧹 Clear memory"):
        st.session_state.chat = []
        st.rerun()

for m in st.session_state.chat:
    with st.chat_message(m["role"]):
        st.write(m["content"])

def clean(text):
    if "</think>" in text:
        return text.split("</think>", 1)[1].strip()
    if "<think>" in text:
        return "🤔 thinking…"
    return text

if prompt := st.chat_input("Say something…"):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.chat.append({"role": "user", "content": prompt})

    messages = [{"role": "system", "content": PERSONALITIES[personality]}] + st.session_state.chat

    with st.chat_message("assistant"), st.spinner("…"):
        stream = client.chat.completions.create(
            model=MODELS[brain], messages=messages, stream=True,
            temperature=creativity, max_tokens=500,
        )
        full = ""
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
        reply = clean(full)
        st.write(reply)

    st.session_state.chat.append({"role": "assistant", "content": reply})
