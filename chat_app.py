import uuid
import requests
import streamlit as st


st.set_page_config(page_title="Shopping Assistant", page_icon="🛍️")
st.title("🛍️ Shopping Assistant")
st.caption("Ask me about products, then follow up with details like sizes, colors, or prices.")

API_URL = "http://localhost:8000/chat"
SESSIONS_URL = "http://localhost:8000/chat/sessions"


def get_or_create_user_id():
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id


def get_or_create_session_id():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        # Create session on backend
        try:
            requests.post(
                SESSIONS_URL,
                json={
                    "user_id": get_or_create_user_id(),
                    "session_id": st.session_state.session_id,
                },
                timeout=10,
            )
        except Exception:
            pass
    return st.session_state.session_id


def ask_agent(message: str) -> str:
    resp = requests.post(
        API_URL,
        json={
            "message": message,
            "user_id": get_or_create_user_id(),
            "session_id": get_or_create_session_id(),
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["response"]


if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("What are you looking for?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = ask_agent(prompt)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
