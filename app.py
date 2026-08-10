import os
import io
import requests
import streamlit as st
from openai import OpenAI
from PIL import Image, ImageEnhance, ImageFilter
from gtts import gTTS

KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(
    page_title="My AI — ULTRA",
    page_icon="🤖",
)

CSS = """
<style>
#MainMenu, footer, header {visibility:hidden;}
.stApp {background:#05070f;}
h1, h2, h3, p, span {color:#e8ecff;}
h1, h2 {
  background: linear-gradient(90deg,#6ea8ff,#a06bff,#ff6ec7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
[data-testid="stChatMessage"] {
  background:#0c1122 !important;
  border:1px solid #232a4d;
  border-radius:18px;
}
[data-testid="stChatInput"] textarea {
  background:#0c1122 !important;
  border:1.5px solid #7b5cff !important;
  border-radius:16px;
  box-shadow:0 0 20px rgba(123,92,255,.35);
  color:#fff !important;
}
.stButton>button {
  background:#141a35;
  color:#cfd6ff;
  border:1px solid #2a3160;
  border-radius:14px;
}
.stButton>button:hover {
  background:#1d2547;
  border-color:#7b5cff;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
if not KEY:
    st.error("Add GROQ_API_KEY in Secrets!")
    st.stop()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=KEY,
)

PERSONALITIES = {
    "🙂 Friendly": "Warm friendly assistant. Short clear answers.",
    "😂 Funny": "Hilarious friend. Humor plus correct answers.",
    "👨‍🏫 Teacher": "World-class teacher. Simple examples.",
    "💻 Coding Pro": "Senior engineer. Precise help.",
}
MODELS = {
    "⚡ Fast": "llama-3.1-8b-instant",
    "🧠 Smart": "qwen/qwen3.6-27b",
}

ss = st.session_state
if "chat" not in ss: ss.chat = []
if "name" not in ss: ss.name = ""
if "tool" not in ss: ss.tool = None

with st.sidebar:
    st.markdown("### ⚙️ Control Center")
    ss.name = st.text_input("Your name", ss.name or "friend")
    pers = st.selectbox("Personality", list(PERSONALITIES))
    brain = st.selectbox("Brain", list(MODELS))
    creat = st.slider("Creativity", 0.0, 1.0, 0.7)
    speak = st.toggle("🔊 Speak replies")
    if st.button("🧹 Clear memory"):
        ss.chat = []
        st.rerun()

def strip_think(t):
    if "</think>" in t:
        return t.split("</think>", 1)[1].strip()
    if "<think>" in t:
        return "🤔 thinking…"
    return t

def get_reply(msgs):
    r = client.chat.completions.create(
        model=MODELS[brain],
        messages=msgs,
        temperature=creat,
        max_tokens=700,    )
    return strip_think(r.choices[0].message.content)

def tts_bytes(text):
    try:
        b = io.BytesIO()
        gTTS(text[:400], lang="en").write_to_fp(b)
        b.seek(0)
        return b.getvalue()
    except Exception:
        return None

tabs = st.tabs(["💬 Chat", "⚡ Tools", "🎨 Image", "🖼️ Edit"])

with tabs[0]:
    st.markdown("## Hello, " + ss.name + " 👋")
    st.caption("How can I help you today?")
    for m in ss.chat:
        with st.chat_message(m["role"]):
            st.write(m["content"])
            if m.get("audio"):
                st.audio(m["audio"], format="audio/mp3")
    audio = st.audio_input("🎤 Speak here")
    voice_text = None
    if audio and st.button("🎤 Send voice"):
        with st.spinner("Listening…"):
            tr = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=("a.wav", audio, "audio/wav"),
            )
            voice_text = tr.text
    p = st.chat_input("Ask anything, explore ideas…")
    user_text = p or voice_text
    if user_text:
        ss.chat.append({"role": "user", "content": user_text})
        msgs = [{"role": "system",
                 "content": PERSONALITIES[pers]}]
        msgs = msgs + ss.chat
        with st.spinner("…"):
            reply = get_reply(msgs)
        newm = {"role": "assistant", "content": reply}
        if speak:
            newm["audio"] = tts_bytes(reply)
        ss.chat.append(newm)
        st.rerun()

with tabs[1]:
    st.markdown("## ⚡ Quick Actions")
    TOOLS = {
        "✍️ Writer": "Write a great short piece about:",        "📋 Summarize": "Summarize in key points:",
        "🌐 Translate": "Translate both Hindi and English:",
        "🧒 Explain": "Explain like I'm 12:",
        "📝 Quiz": "5 MCQs, answers at end, on:",
        "🃏 Cards": "8 flashcards Q:/A: on:",
        "🗓️ Plan": "7-day study plan for:",
        "💻 Code": "Write code for:",
        "🐞 Fix": "Fix bugs and explain:",
    }
    names = list(TOOLS)
    for row in range(0, len(names), 3):
        cols = st.columns(3)
        for i, c in enumerate(cols):
            idx = row + i
            if idx < len(names):
                nm = names[idx]
                if c.button(nm, key=nm):
                    ss.tool = nm
                    st.rerun()
    if ss.tool:
        st.markdown("### " + ss.tool)
        task = st.text_area("Topic / text / code")
        if st.button("🚀 Go"):
            with st.spinner("…"):
                r = get_reply([{"role": "user",
                    "content": TOOLS[ss.tool] + " " + task}])
            st.markdown(r)

with tabs[2]:
    st.markdown("## 🎨 Image Generator")
    ip = st.text_input(
        "Describe your image",
        "Cyberpunk city, neon lights",
    )
    if st.button("✨ Create image"):
        with st.spinner("Painting… (20-40 sec)"):
            url = "https://image.pollinations.ai/prompt/"
            url += requests.utils.quote(ip)
            url += "?width=768&height=768&nologo=true"
            st.image(url, caption=ip)
            st.markdown("[⬇️ Download](" + url + ")")

with tabs[3]:
    st.markdown("## 🖼️ Photo Editor")
    up = st.file_uploader(
        "Upload a photo",
        type=["png", "jpg", "jpeg"],
    )
    if up:
        img = Image.open(up).convert("RGB")
        st.image(img, caption="Original")
        g = st.toggle("⬛ Black & white")
        br = st.slider("☀️ Brightness", 0.5, 2.0, 1.0)
        co = st.slider("🎚️ Contrast", 0.5, 2.0, 1.0)
        bl = st.toggle("🌫️ Soft blur")
        if g:
            out = img.convert("L").convert("RGB")
        else:
            out = img
        out = ImageEnhance.Brightness(out).enhance(br)
        out = ImageEnhance.Contrast(out).enhance(co)
        if bl:
            out = out.filter(ImageFilter.BLUR)
        st.image(out, caption="Edited ✨")
        b = io.BytesIO()
        out.save(b, "PNG")
        st.download_button(
            "⬇️ Download",
            b.getvalue(),
            "edited.png",
            "image/png",
        )
