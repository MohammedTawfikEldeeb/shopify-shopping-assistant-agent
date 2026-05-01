import requests
import streamlit as st


st.set_page_config(page_title="Shopping Assistant", page_icon="🛍️")
st.title("🛍️ Shopping Assistant")
st.caption("Ask me about products, then follow up with details like sizes, colors, or prices.")

API_URL = "http://localhost:8000/chat"


def ask_agent(message: str) -> str:
    resp = requests.post(API_URL, json={"message": message}, timeout=60)
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
