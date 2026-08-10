import os
import io
import requests
import streamlit as st
from openai import OpenAI
from PIL import Image, ImageEnhance, ImageFilter
from gtts import gTTS

KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(
    page_title="My AI App ULTRA",
    page_icon="🚀",
)

CSS = """
<style>
#MainMenu, footer, header {visibility: hidden;}
h1 {
  background: linear-gradient(90deg,#ff8a00,#e60073,#7b2ff7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
st.title("🚀 My AI App — ULTRA")

if not KEY:
    st.error("Add GROQ_API_KEY in Secrets!")
    st.stop()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=KEY,
)

PERSONALITIES = {
    "🙂 Friendly Helper": "Warm friendly assistant. Short clear answers.",
    "😂 Funny Friend": "Hilarious friend. Humor plus correct answers, short.",
    "👨‍🏫 Great Teacher": "World-class teacher. Simple examples for a 12 year old.",
    "💻 Coding Pro": "Senior engineer. Precise help, short code examples.",
}

MODELS = {
    "⚡ Fast": "llama-3.1-8b-instant",
    "🧠 Smart": "qwen/qwen3.6-27b",
}

if "chat" not in st.session_state:
    st.session_state.chat = []

with st.sidebar:
    st.markdown("### ⚙️ Control Center")
    pers = st.selectbox("Personality", list(PERSONALITIES))
    brain = st.selectbox("Brain", list(MODELS))
    creat = st.slider("Creativity", 0.0, 1.0, 0.7)
    speak = st.toggle("🔊 Speak replies")
    if st.button("🧹 Clear memory"):
        st.session_state.chat = []
        st.rerun()

def clean(t):
    if "</think>" in t:
        return t.split("</think>", 1)[1].strip()
    if "<think>" in t:
        return "🤔 thinking…"
    return t

def ask(user_text):
    with st.chat_message("user"):
        st.write(user_text)
    st.session_state.chat.append(
        {"role": "user", "content": user_text}
    )
    msgs = [{"role": "system",
             "content": PERSONALITIES[pers]}]
    msgs = msgs + st.session_state.chat
    with st.chat_message("assistant"):
        with st.spinner("…"):
            stream = client.chat.completions.create(
                model=MODELS[brain],
                messages=msgs,
                stream=True,
                temperature=creat,
                max_tokens=600,
            )
            full = ""
            for c in stream:
                ok = c.choices and c.choices[0].delta.content
                if ok:
                    full += c.choices[0].delta.content
            reply = clean(full)
            st.write(reply)
            if speak:
                try:
                    buf = io.BytesIO()
                    gTTS(reply, lang="en").write_to_fp(buf)
                    buf.seek(0)
                    st.audio(buf, format="audio/mp3")
                except Exception:
                    pass
    st.session_state.chat.append(
        {"role": "assistant", "content": reply}
    )

def study(prompt, title):
    with st.spinner("…"):
        r = client.chat.completions.create(
            model=MODELS["⚡ Fast"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
        )
        r = r.choices[0].message.content
    st.markdown("### " + title)
    st.markdown(r)

tabs = st.tabs([
    "💬 Chat",
    "🎨 Create Image",
    "🖼️ Edit Photo",
    "📚 Study",
    "💻 Code",
])

with tabs[0]:
    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.write(m["content"])
    audio = st.audio_input("🎤 Or speak here")
    if audio and st.button("🎤 Send my voice"):
        with st.spinner("Listening…"):
            tr = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=("a.wav", audio, "audio/wav"),
            )
            tr = tr.text
        ask(tr)
    p = st.chat_input("Say something…")
    if p:
        ask(p)

with tabs[1]:
    ip = st.text_input(
        "Describe your image 🎨",
        "A tiger astronaut on the moon, digital art",
    )
    if st.button("✨ Create image"):
        with st.spinner("Painting… (20-40 sec)"):
            url = "https://image.pollinations.ai/prompt/"
            url += requests.utils.quote(ip)
            url += "?width=768&height=768&nologo=true"
            st.image(url, caption=ip)
            st.markdown("[⬇️ Download image](" + url + ")")

with tabs[2]:
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

with tabs[3]:
    topic = st.text_input(
        "What are you studying? 📚",
        "Photosynthesis",
    )
    c1, c2 = st.columns(2)
    if c1.button("🧒 Explain simply"):
        study("Explain like I'm 12, with examples: " + topic,
              "🧒 Simple explanation")
    if c2.button("📝 Quiz me"):
        study("Give 5 MCQ questions on " + topic +
              ". Put answers at the end.", "📝 Quiz")
    if c1.button("🃏 Flashcards"):
        study("Make 8 flashcards (Q: / A:) about " + topic,
              "🃏 Flashcards")
    if c2.button("🗓️ Study plan"):
        study("Make a 7-day study plan to master " + topic,
              "🗓️ Plan")

with tabs[4]:
    mode = st.selectbox("Mode", [
        "✍️ Write code",
        "🐞 Fix my code",
        "📖 Explain code",
    ])
    task = st.text_area("Describe task / paste code")
    if st.button("🚀 Go"):
        if mode == "✍️ Write code":
            pr = "Write code: " + task
        elif mode == "🐞 Fix my code":
            pr = "Fix bugs and explain: " + task
        else:
            pr = "Explain line by line: " + task
        study(pr, "💻 Result")
