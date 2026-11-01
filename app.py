"""AI Chat Application - Streamlit UI.

Run with:  streamlit run app.py
"""
import streamlit as st

from chat_core import (
    DEFAULT_SYSTEM_PROMPT,
    MODELS,
    chat,
    get_client,
    summarize_chat_json,
)

st.set_page_config(page_title="AI Chat Assistant", page_icon="🤖")
st.title("🤖 AI Chat Assistant")
st.caption("Built with the Gemini API | Codomax Digital Solutions - Module 3")

# ---------- Session state (keeps history between messages) ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "usage" not in st.session_state:
    st.session_state.usage = {"input": 0, "output": 0, "cost": 0.0}

# ---------- API client ----------
try:
    client = get_client()
except RuntimeError as e:
    st.error(str(e))
    st.stop()

# ---------- Sidebar: custom instructions and parameters ----------
with st.sidebar:
    st.header("Settings")
    system_prompt = st.text_area(
        "Custom instructions (system prompt)", value=DEFAULT_SYSTEM_PROMPT, height=130
    )
    model = st.selectbox("Model", MODELS)
    temperature = st.slider("Temperature (creativity)", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.slider("Max output tokens", 100, 2048, 1024, 50)

    st.divider()
    st.subheader("Usage (this session)")
    u = st.session_state.usage
    st.write(f"Input tokens: **{u['input']}**")
    st.write(f"Output tokens: **{u['output']}**")
    st.write(f"Estimated cost: **${u['cost']:.5f}**")

    st.divider()
    if st.button("Summarize chat (JSON)") and st.session_state.messages:
        try:
            st.json(summarize_chat_json(client, st.session_state.messages, model))
        except RuntimeError as e:
            st.error(str(e))

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.session_state.usage = {"input": 0, "output": 0, "cost": 0.0}
        st.rerun()

# ---------- Show previous messages ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------- User input and AI response ----------
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = chat(
                    client, st.session_state.messages, system_prompt,
                    model, temperature, max_tokens,
                )
                st.markdown(result["text"])
                st.session_state.messages.append(
                    {"role": "assistant", "content": result["text"]}
                )
                st.session_state.usage["input"] += result["input_tokens"]
                st.session_state.usage["output"] += result["output_tokens"]
                st.session_state.usage["cost"] += result["cost"]
                st.rerun()
            except RuntimeError as e:
                st.error(str(e))
                st.session_state.messages.pop()  # remove unanswered question
