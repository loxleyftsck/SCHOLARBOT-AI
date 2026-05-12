import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ─── Page Config ───────────────────────────────────────────────────────────────
from config.settings import APP_TITLE, APP_ICON, APP_LAYOUT, APP_SIDEBAR_STATE
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=APP_LAYOUT,
    initial_sidebar_state=APP_SIDEBAR_STATE,
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
from ui.styles import CSS
st.markdown(CSS, unsafe_allow_html=True)

# ─── Core Imports ─────────────────────────────────────────────────────────────
from core import (
    call_llama,
    extract_topic,
    set_api_key,
    init_defaults,
    reset_chat,
    build_memory_card_html,
    API_KEY as CORE_API_KEY,
)
from prompts import PERSONALITIES, MODES

# ─── Utils Imports ─────────────────────────────────────────────────────────────
# Phase 6: Wire in validators + token counter
from utils.validators import is_safe_message, validate_message
from utils.token_counter import is_within_limit, truncate_messages

# ─── Storage Imports ───────────────────────────────────────────────────────────
# Phase 6: Wire in JSON persistence
from storage import save_session, get_storage_stats

# ─── Suggestion Chips (defined as data, not HTML) ─────────────────────────────
# Engineering decision: data-driven chips = easy to add/remove
SUGGESTION_CHIPS = [
    ("📐", "Jelaskan teorema Pythagoras"),
    ("🌏", "Rangkum Perang Dunia II"),
    ("💻", "Apa itu machine learning?"),
    ("🧪", "Buat soal Kimia Kelas 12"),
]

# ─── Session State Init ───────────────────────────────────────────────────────
defaults = init_defaults()
defaults["session_start"] = "init"
defaults["chip_input"] = None  # NEW: track clicked chip text
for key, default_val in defaults.items():
    if key == "session_start":
        from datetime import datetime
        st.session_state.setdefault(key, datetime.now().strftime("%H:%M"))
    else:
        st.session_state.setdefault(key, default_val)

# ─── Sidebar Config ───────────────────────────────────────────────────────────
from ui.sidebar import (
    HEADER_HTML,
    SECTION_LABELS,
    GROQ_KEY_HELP,
    GROQ_KEY_PH,
    NAME_PLACEHOLDER,
    CHAT_PLACEHOLDER_DEFAULT,
    memory_card_html,
)

# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(HEADER_HTML, unsafe_allow_html=True)

    # API Key input
    if not CORE_API_KEY:
        st.markdown(f'<div class="sidebar-label">{SECTION_LABELS["api_key"]}</div>',
                    unsafe_allow_html=True)
        st.caption(GROQ_KEY_HELP)
        key_input = st.text_input(
            "Groq API Key", type="password", placeholder=GROQ_KEY_PH,
            label_visibility="collapsed",
        )
        if key_input:
            set_api_key(key_input)
            st.success("✓ API Key Groq tersimpan!")
        st.markdown("---")

    # User name
    st.markdown(f'<div class="sidebar-label">{SECTION_LABELS["profile"]}</div>',
                unsafe_allow_html=True)
    name = st.text_input(
        "Nama kamu",
        value=st.session_state.user_name,
        placeholder=NAME_PLACEHOLDER,
        label_visibility="collapsed",
    )
    if name != st.session_state.user_name:
        st.session_state.user_name = name

    # Personality selector
    st.markdown(f'<div class="sidebar-label">{SECTION_LABELS["personality"]}</div>',
                unsafe_allow_html=True)
    persona_keys = list(PERSONALITIES.keys())
    try:
        persona_index = persona_keys.index(st.session_state.personality)
    except ValueError:
        persona_index = 0
    persona = st.selectbox(
        "Personality", persona_keys,
        index=persona_index,
        label_visibility="collapsed",
    )
    if persona != st.session_state.personality:
        st.session_state.personality = persona
    p_info = PERSONALITIES[persona]
    st.markdown(
        f'<div style="font-size:0.75rem;color:#718096;padding:4px 4px 12px;">'
        f'<b style="color:#63b3ed">{p_info["label"]}</b> — {p_info["desc"]}</div>',
        unsafe_allow_html=True,
    )

    # Mode buttons
    st.markdown(f'<div class="sidebar-label">{SECTION_LABELS["modes"]}</div>',
                unsafe_allow_html=True)
    for mode_label in MODES:
        if st.button(mode_label, key=f"mode_{mode_label}", use_container_width=True):
            st.session_state.active_mode = mode_label

    st.markdown("---")

    # Memory card
    st.markdown(f'<div class="sidebar-label">{SECTION_LABELS["memory"]}</div>',
                unsafe_allow_html=True)
    st.markdown(memory_card_html(dict(st.session_state)), unsafe_allow_html=True)

    # Storage stats (Phase 6)
    stats = get_storage_stats()
    if stats.sessions_count > 0:
        size_kb = stats.total_size_bytes / 1024
        st.caption(f"📁 {stats.sessions_count} sesi tersimpan ({size_kb:.1f} KB)")

    st.markdown("---")
    if st.button("🗑️ Reset Chat", use_container_width=True):
        for k, v in reset_chat(dict(st.session_state)).items():
            st.session_state[k] = v
        st.rerun()

# ─── MAIN AREA ──────────────────────────────────────────────────────────────────
st.markdown('<div class="main-wrapper">', unsafe_allow_html=True)

# ─── Welcome Screen with Clickable Suggestion Chips ───────────────────────────
# FIX: Replace fake HTML chips with real st.button widgets
# Each button click stores prompt text in session_state.chip_input
if not st.session_state.messages:
    greeting = f"Halo, {st.session_state.user_name}! " if st.session_state.user_name else ""
    st.markdown(f"""
    <div class="welcome-block">
        <div class="welcome-icon">🎓</div>
        <div class="welcome-title">ScholarBot AI</div>
        <div class="welcome-sub">
            {greeting}Asisten belajar cerdas yang siap membantumu memahami materi,<br>
            membuat rangkuman, quiz, dan banyak lagi.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Render chips as real Streamlit buttons in 2-column grid
    # Each row: 2 chips side by side
    chips_per_row = 2
    for i in range(0, len(SUGGESTION_CHIPS), chips_per_row):
        cols = st.columns(chips_per_row)
        for j, (icon, text) in enumerate(SUGGESTION_CHIPS[i:i + chips_per_row]):
            with cols[j]:
                # st.button = real clickable widget
                # key = unique per chip so Streamlit tracks state
                # on_click approach: just check session_state after rerun
                if st.button(f"{icon} {text}", key=f"chip_{i+j}", use_container_width=True):
                    # Store chip text in session_state — will be processed on rerun
                    st.session_state.chip_input = text
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

# ─── Process Chip Click ────────────────────────────────────────────────────────
# If a chip was clicked, treat it as user input
# Engineering: This runs BEFORE st.chat_input, so chip triggers API call on same rerun
chip_input = st.session_state.get("chip_input")
if chip_input:
    st.session_state.chip_input = None  # Clear immediately to prevent double-trigger

    # Prepend mode prefix if a learning mode is active
    final_input = chip_input
    if st.session_state.active_mode:
        mode_text = MODES[st.session_state.active_mode]
        if not chip_input.startswith(mode_text):
            final_input = mode_text + " " + chip_input
        st.session_state.active_mode = None

    # Validate input (Phase 6)
    if not is_safe_message(final_input):
        validation = validate_message(final_input)
        st.error(validation.message)
    else:
        # Track topic
        topic = extract_topic(final_input)
        if topic and topic not in st.session_state.topics_discussed:
            st.session_state.topics_discussed.append(topic)

        # Append user message
        from datetime import datetime
        now = datetime.now().strftime("%H:%M")
        st.session_state.messages.append(
            {"role": "user", "content": final_input, "time": now}
        )
        st.session_state.msg_count += 1

        # Call LLM with token safety check (Phase 6)
        conversation_history = st.session_state.messages[:-1]
        if not is_within_limit(conversation_history):
            conversation_history = truncate_messages(conversation_history)
            st.session_state.messages = (
                conversation_history
                + [st.session_state.messages[-1]]
            )

        with st.spinner(""):
            reply = call_llama(
                user_msg=final_input,
                personality_key=st.session_state.personality,
                user_name=st.session_state.user_name,
                topics=st.session_state.topics_discussed,
                conversation_history=st.session_state.messages[:-1],
            )

        st.session_state.messages.append(
            {"role": "assistant", "content": reply, "time": datetime.now().strftime("%H:%M")}
        )

        # Persist to JSON (Phase 6)
        save_session("default", dict(st.session_state))

        st.rerun()

# ─── Render Chat History ────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    is_user = msg["role"] == "user"
    row_cls = "user" if is_user else "bot"
    avatar  = "👤" if is_user else "🎓"
    bubble_cls = "user" if is_user else "bot"
    st.markdown(f"""
    <div class="msg-row {row_cls}">
        <div class="avatar {row_cls}">{avatar}</div>
        <div>
            <div class="bubble {bubble_cls}">{msg["content"]}</div>
            <div class="msg-time">{msg.get("time", "")}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ─── Chat Input ─────────────────────────────────────────────────────────────────
active_mode = st.session_state.get("active_mode")
mode_prefix = MODES.get(active_mode, "") if active_mode else ""
placeholder = mode_prefix or CHAT_PLACEHOLDER_DEFAULT

user_input = st.chat_input(placeholder=placeholder)

if user_input:
    final_input = user_input
    if active_mode:
        mode_text = MODES[active_mode]
        if not user_input.startswith(mode_text):
            final_input = mode_text + " " + user_input
        st.session_state.active_mode = None

    # Validate input (Phase 6)
    if not is_safe_message(final_input):
        validation = validate_message(final_input)
        st.error(validation.message)
    else:
        # Track topic
        topic = extract_topic(final_input)
        if topic and topic not in st.session_state.topics_discussed:
            st.session_state.topics_discussed.append(topic)

        # Append user message
        from datetime import datetime
        now = datetime.now().strftime("%H:%M")
        st.session_state.messages.append(
            {"role": "user", "content": final_input, "time": now}
        )
        st.session_state.msg_count += 1

        # Call LLM with token safety check (Phase 6)
        conversation_history = st.session_state.messages[:-1]
        if not is_within_limit(conversation_history):
            conversation_history = truncate_messages(conversation_history)
            st.session_state.messages = (
                conversation_history
                + [st.session_state.messages[-1]]
            )

        with st.spinner(""):
            reply = call_llama(
                user_msg=final_input,
                personality_key=st.session_state.personality,
                user_name=st.session_state.user_name,
                topics=st.session_state.topics_discussed,
                conversation_history=st.session_state.messages[:-1],
            )

        st.session_state.messages.append(
            {"role": "assistant", "content": reply, "time": datetime.now().strftime("%H:%M")}
        )

        # Persist to JSON (Phase 6)
        save_session("default", dict(st.session_state))

        st.rerun()
