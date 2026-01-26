import streamlit as st
from engine import start_session, step, should_stop, evaluate


# Page config

st.set_page_config(
    page_title="Feynman AI",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# Custom CSS

st.markdown(
    """
    <style>
    /* Global background */
    .stApp {
        background-color: #0e1117;
        color: #e6e6e6;
    }

    /* Center column width */
    section.main > div {
        max-width: 720px;
    }

    /* Header title */
    .feynman-title {
        font-size: 2.2rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 0.25rem;
    }

    .feynman-subtitle {
        font-size: 0.95rem;
        color: #9aa4b2;
        margin-bottom: 1.5rem;
    }

    /* Chat bubbles */
    .stChatMessage {
        padding: 0.6rem 0.8rem;
        border-radius: 8px;
    }

    /* User messages */
    div[data-testid="chat-message-user"] {
        background-color: #1c1f26;
        border-left: 3px solid #3ddc97;
    }

    /* Assistant messages */
    div[data-testid="chat-message-assistant"] {
        background-color: #141821;
        border-left: 3px solid #5fa8ff;
    }

    /* Chat input */
    textarea {
        background-color: #0b0e14 !important;
        color: #e6e6e6 !important;
        border-radius: 8px !important;
        border: 1px solid #2a2f3a !important;
    }

    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #2a2f3a, transparent);
        margin: 2rem 0;
    }

    /* End analysis box */
    .analysis-box {
        background-color: #0b0e14;
        padding: 1.25rem;
        border-radius: 10px;
        border: 1px solid #2a2f3a;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Header

st.markdown('<div class="feynman-title">Feynman AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="feynman-subtitle">'
    'Explain a concept. I will challenge it until it breaks—or holds.'
    '</div>',
    unsafe_allow_html=True
)


# Session state

if "history" not in st.session_state:
    st.session_state.history = start_session()

if "awaiting_response" not in st.session_state:
    st.session_state.awaiting_response = False

if "pending_user_input" not in st.session_state:
    st.session_state.pending_user_input = None

if "finished" not in st.session_state:
    st.session_state.finished = False


# Render chat history

for msg in st.session_state.history:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])


# Input

if not st.session_state.finished:
    user_input = st.chat_input("Explain a concept in your own words…")

    if user_input and not st.session_state.awaiting_response:
        if should_stop(user_input):
            st.session_state.finished = True
            st.rerun()

        st.session_state.pending_user_input = user_input
        st.session_state.awaiting_response = True
        st.rerun()

# Echo user input immediately

if st.session_state.awaiting_response and st.session_state.pending_user_input:
    with st.chat_message("user"):
        st.write(st.session_state.pending_user_input)


# Engine step

if st.session_state.awaiting_response and st.session_state.pending_user_input:
    _, st.session_state.history = step(
        st.session_state.history,
        st.session_state.pending_user_input
    )

    st.session_state.pending_user_input = None
    st.session_state.awaiting_response = False
    st.rerun()


# End of session analysis

if st.session_state.finished:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("End of Session Analysis")

    st.markdown(
        f"""
        <div class="analysis-box">
        {evaluate(st.session_state.history)}
        </div>
        """,
        unsafe_allow_html=True
    )
