import streamlit as st
from engine import start_session, step, should_stop, evaluate


st.set_page_config(page_title="Feynman AI", layout="centered")


if "history" not in st.session_state:
    st.session_state.history = start_session()

if "awaiting_response" not in st.session_state:
    st.session_state.awaiting_response = False

if "pending_user_input" not in st.session_state:
    st.session_state.pending_user_input = None

if "finished" not in st.session_state:
    st.session_state.finished = False


for msg in st.session_state.history:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])


if not st.session_state.finished:
    user_input = st.chat_input("Explain a concept...")

    if user_input and not st.session_state.awaiting_response:
        
        if should_stop(user_input):
            st.session_state.finished = True
            st.rerun()

        
        st.session_state.pending_user_input = user_input
        st.session_state.awaiting_response = True
        st.rerun()


if st.session_state.awaiting_response and st.session_state.pending_user_input:
    with st.chat_message("user"):
        st.write(st.session_state.pending_user_input)


if st.session_state.awaiting_response and st.session_state.pending_user_input:
    _, st.session_state.history = step(
        st.session_state.history,
        st.session_state.pending_user_input
    )

   
    st.session_state.pending_user_input = None
    st.session_state.awaiting_response = False

    st.rerun()


if st.session_state.finished:
    st.divider()
    st.subheader("End of Session Analysis")
    st.write(evaluate(st.session_state.history))
