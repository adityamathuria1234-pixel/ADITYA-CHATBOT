import streamlit as st
from groq import Groq
from datetime import datetime
import hashlib
import time

st.set_page_config(page_title="Aditya's Chatbot", page_icon="💬", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Work+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Work Sans', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: #F3F5F1;
}

[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E2E6E1;
}

.hero h1 {
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 36px;
    letter-spacing: -0.5px;
    color: #1B2A24;
    margin: 6px 0 4px 0;
}
.hero p {
    font-size: 15px;
    color: #5B6660;
    margin: 0 0 14px 0;
}
.hero hr {
    border: none;
    border-top: 2px solid #2F6F5E;
    width: 44px;
    margin: 0 0 26px 0;
}

[data-testid="stChatMessage"] {
    background: #FFFFFF;
    border: 1px solid #E2E6E1;
    border-radius: 12px;
    padding: 4px 12px;
    margin-bottom: 10px;
}

[data-testid="stAudioInput"] {
    border-radius: 12px;
    margin-bottom: 10px;
}

[data-testid="stChatInput"] {
    border: 2px solid #2F6F5E;
    border-radius: 14px;
    background: #FFFFFF;
    box-shadow: 0 0 0 3px rgba(47, 111, 94, 0.15);
    transition: box-shadow 0.15s ease;
}
[data-testid="stChatInput"]:focus-within {
    box-shadow: 0 0 0 4px rgba(47, 111, 94, 0.28);
}
[data-testid="stChatInput"] textarea {
    border-radius: 12px;
}

.stButton > button {
    background: #2F6F5E;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    padding: 6px 16px;
}
.stButton > button:hover {
    background: #24564A;
    color: #FFFFFF;
}
</style>
""", unsafe_allow_html=True)

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.markdown("""
<div class="hero">
    <h1>Aditya's Chatbot</h1>
    <p>A personal chatbot you can ask anything.</p>
    <hr>
</div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    avatar = "🙂" if msg["role"] == "user" else "💬"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])
        st.caption(msg["time"])

prompt = st.chat_input("Ask me a question...")

audio = st.audio_input("🎙️ Or ask by voice")
if audio is not None:
    audio_bytes = audio.getvalue()
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    if audio_hash != st.session_state.get("last_audio_hash"):
        st.session_state.last_audio_hash = audio_hash
        with st.spinner("Transcribing..."):
            try:
                transcription = client.audio.transcriptions.create(
                    file=("voice.wav", audio_bytes),
                    model="whisper-large-v3-turbo",
                    response_format="json"
                )
                prompt = transcription.text
            except Exception as e:
                st.error(f"Couldn't transcribe that: {e}")

if prompt:
    now = datetime.now().strftime("%I:%M %p")
    st.session_state.messages.append({"role": "user", "content": prompt, "time": now})
    with st.chat_message("user", avatar="🙂"):
        st.write(prompt)
        st.caption(now)

    with st.chat_message("assistant", avatar="💬"):
        with st.spinner("Typing..."):
            start = time.perf_counter()
            try:
                api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    max_tokens=500,
                    messages=api_messages
                )
                reply = response.choices[0].message.content
            except Exception as e:
                reply = f"Error: {str(e)}"
            elapsed = time.perf_counter() - start
        reply_time = datetime.now().strftime("%I:%M %p")
        st.write(reply)
        st.caption(reply_time)

    st.session_state.messages.append({"role": "assistant", "content": reply, "time": reply_time})
    st.session_state.last_response_seconds = elapsed

with st.sidebar:
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()
    if "last_response_seconds" in st.session_state:
        st.caption(f"Last response took {st.session_state.last_response_seconds:.2f}s")