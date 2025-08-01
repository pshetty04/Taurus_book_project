# pages/chatbot.py

import streamlit as st
from backend.p_chatbot import answer # Corrected import

def render_page():
    st.header("Book-Bot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask me: e.g. Define 'ephemeral', or Plot of '1984'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.spinner("Thinking..."):
            reply = answer(prompt)
        
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)