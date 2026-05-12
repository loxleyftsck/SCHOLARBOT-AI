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
from core.session_helpers import (
    detect_intent,
    is_quiz_request,
    extract_answer_from_response,
)
from core.memory_manager import reset_rag_docs
from prompts import PERSONALITIES, MODES

# ─── Utils Imports ─────────────────────────────────────────────────────────────
from utils.validators import is_safe_message, validate_message
from utils.token_counter import is_within_limit, truncate_messages

# ─── Storage Imports ───────────────────────────────────────────────────────────
from storage import save_session, get_storage_stats

# ─── Services Imports (v3 RAG) ─────────────────────────────────────────────────
from services import (
    extract_document,
    get_document_info,
    chunk_text,
    retrieve,
)
from services.retriever import RetrievedChunk
from ui.uploader import (
    RAG_SECTION_LABEL,
    CLEAR_DOCS_LABEL,
    build_upload_status_html,
    build_upload_error_html,
    get_file_extension,
)

# ─── Suggestion Chips ──────────────────────────────────────────────────────────
SUGGESTION_CHIPS = [
    ("📐", "Jelaskan teorema Pythagoras"),
    ("🌏", "Rangkum Perang Dunia II"),
    ("💻", "Apa itu machine learning?"),
    ("🧪", "Buat soal Kimia Kelas 12"),
]

# ─── Session State Init ───────────────────────────────────────────────────────
defaults = init_defaults()
defaults["session_start"] = "init"
defaults["chip_input"] = None
defaults["rag_error"] = None  # v3: upload error message
defaults["rag_processing"] = False  # v3: processing indicator
for key, default_val in defaults.items():
    if key == "session_start":
        from datetime import datetime
        st.session_state.setdefault(key, datetime.now().strftime("%H:%M"))
    else:
        st.session_state.setdefault(key, default_val)

# ─── Callbacks ─────────────────────────────────────────────────────────────────

def _reset_chat_callback():
    """Safe reset: clears conversation, keeps profile + RAG documents."""
    st.session_state.messages = []
    st.session_state.topics_discussed = []
    st.session_state.msg_count = 0
    st.session_state.active_mode = None
    st.session_state.chip_input = None
    st.session_state.last_question = ""
    st.session_state.last_answer = ""
    st.session_state.current_context = ""
    st.session_state.awaiting_followup = False


def _set_mode_callback(mode: str):
    """Callback to set active learning mode."""
    st.session_state.active_mode = mode


def _set_chip_input_callback(text: str):
    """Callback to set chip input for processing."""
    st.session_state.chip_input = text


def _clear_docs_callback():
    """Clear all uploaded RAG documents."""
    reset_rag_docs(st.session_state)
    st.session_state.rag_error = None


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
        st.button(
            mode_label,
            key=f"mode_{mode_label}",
            on_click=_set_mode_callback,
            args=(mode_label,),
            use_container_width=True
        )

    # ── v3 RAG: Document Uploader ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f'<div class="sidebar-label">{RAG_SECTION_LABEL}</div>',
                unsafe_allow_html=True)

    # Upload widget
    uploaded_files = st.file_uploader(
        "Upload .txt atau .pdf",
        type=["txt", "pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="Upload materi belajar (.txt atau .pdf) untuk digunakan sebagai konteks chatbot.",
    )

    # Process uploaded files
    if uploaded_files:
        st.session_state.rag_error = None
        existing_names = {d["filename"] for d in st.session_state.uploaded_docs}

        for file in uploaded_files:
            fname = file.name
            # Skip duplicates
            if fname in existing_names:
                continue

            try:
                file_bytes = file.getvalue()
                file_ext = get_file_extension(fname)

                # Extract text
                text = extract_document(file_bytes, fname, file_ext)

                # Chunk text
                chunks = chunk_text(text, strategy="auto", filename=fname)

                # Store metadata
                info = get_document_info(text, fname)
                doc_meta = {
                    "filename": fname,
                    "size": len(file_bytes),
                    "type": file_ext,
                    "char_count": info["char_count"],
                    "chunk_count": len(chunks),
                }
                st.session_state.uploaded_docs.append(doc_meta)

                # Store raw text
                st.session_state.doc_texts.append(text)

                # Store chunks as dicts (not Chunk objects — not JSON-serializable)
                for chunk in chunks:
                    st.session_state.doc_chunks.append({
                        "content": chunk.content,
                        "source": chunk.source_filename,
                        "index": chunk.chunk_index,
                    })

            except ValueError as e:
                st.session_state.rag_error = str(e)

    # Upload status / error display
    if st.session_state.rag_error:
        st.markdown(build_upload_error_html(st.session_state.rag_error), unsafe_allow_html=True)
        st.session_state.rag_error = None  # Clear after showing once
    elif st.session_state.uploaded_docs:
        st.markdown(build_upload_status_html(st.session_state.uploaded_docs), unsafe_allow_html=True)

    # Clear docs button (only show if docs exist)
    if st.session_state.uploaded_docs:
        st.button(
            CLEAR_DOCS_LABEL,
            key="clear_docs_btn",
            on_click=_clear_docs_callback,
            use_container_width=True,
        )

    st.markdown("---")

    # Memory card
    st.markdown(f'<div class="sidebar-label">{SECTION_LABELS["memory"]}</div>',
                unsafe_allow_html=True)
    st.markdown(memory_card_html(dict(st.session_state)), unsafe_allow_html=True)

    # Storage stats
    stats = get_storage_stats()
    if stats.sessions_count > 0:
        size_kb = stats.total_size_bytes / 1024
        st.caption(f"📁 {stats.sessions_count} sesi tersimpan ({size_kb:.1f} KB)")

    st.markdown("---")
    st.button("🗑️ Reset Chat", use_container_width=True, on_click=_reset_chat_callback)

# ─── MAIN AREA ──────────────────────────────────────────────────────────────────
st.markdown('<div class="main-wrapper">', unsafe_allow_html=True)

# ─── Welcome Screen ────────────────────────────────────────────────────────────
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

    chips_per_row = 2
    for i in range(0, len(SUGGESTION_CHIPS), chips_per_row):
        cols = st.columns(chips_per_row)
        for j, (icon, text) in enumerate(SUGGESTION_CHIPS[i:i + chips_per_row]):
            with cols[j]:
                st.button(
                    f"{icon} {text}",
                    key=f"chip_{i+j}",
                    on_click=_set_chip_input_callback,
                    args=(text,),
                    use_container_width=True
                )

    st.markdown("<br>", unsafe_allow_html=True)

# ─── Process Chip Click ────────────────────────────────────────────────────────
chip_input = st.session_state.get("chip_input")
if chip_input:
    st.session_state.chip_input = None

    final_input = chip_input
    if st.session_state.active_mode:
        mode_text = MODES[st.session_state.active_mode]
        if not chip_input.startswith(mode_text):
            final_input = mode_text + " " + chip_input
        st.session_state.active_mode = None

    if not is_safe_message(final_input):
        validation = validate_message(final_input)
        st.error(validation.message)
    else:
        topic = extract_topic(final_input)
        if topic and topic not in st.session_state.topics_discussed:
            st.session_state.topics_discussed.append(topic)

        from datetime import datetime
        now = datetime.now().strftime("%H:%M")
        st.session_state.messages.append(
            {"role": "user", "content": final_input, "time": now}
        )
        st.session_state.msg_count += 1

        conversation_history = st.session_state.messages[:-1]
        if not is_within_limit(conversation_history):
            conversation_history = truncate_messages(conversation_history)
            st.session_state.messages = (
                conversation_history
                + [st.session_state.messages[-1]]
            )

        # v3 RAG: retrieve relevant chunks before calling LLM
        retrieved_chunks = []
        if st.session_state.doc_chunks:
            from services.chunker import Chunk
            chunks = [
                Chunk(content=c["content"], source_filename=c["source"], chunk_index=c["index"])
                for c in st.session_state.doc_chunks
            ]
            retrieved = retrieve(final_input, chunks, top_k=3)
            # Convert RetrievedChunk to dict for session state
            retrieved_chunks = retrieved
            st.session_state.last_retrieved = [
                {"content": r.content, "score": r.score, "source": r.source_filename, "index": r.chunk_index}
                for r in retrieved
            ]

        with st.spinner(""):
            reply = call_llama(
                user_msg=final_input,
                personality_key=st.session_state.personality,
                user_name=st.session_state.user_name,
                topics=st.session_state.topics_discussed,
                conversation_history=st.session_state.messages[:-1],
                current_context=st.session_state.current_context,
                last_question=st.session_state.last_question,
                last_answer=st.session_state.last_answer,
                retrieved_chunks=retrieved_chunks,
            )

        st.session_state.messages.append(
            {"role": "assistant", "content": reply, "time": datetime.now().strftime("%H:%M")}
        )

        if is_quiz_request(final_input):
            st.session_state.current_context = "quiz"
            st.session_state.last_question = final_input[:200]
            st.session_state.last_answer = extract_answer_from_response(reply)

        intent = detect_intent(final_input.lower())
        if intent in ("give_answer", "give_explanation") and st.session_state.last_question:
            if intent == "give_answer":
                st.session_state.last_answer = reply[:500]

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

    if not is_safe_message(final_input):
        validation = validate_message(final_input)
        st.error(validation.message)
    else:
        topic = extract_topic(final_input)
        if topic and topic not in st.session_state.topics_discussed:
            st.session_state.topics_discussed.append(topic)

        from datetime import datetime
        now = datetime.now().strftime("%H:%M")
        st.session_state.messages.append(
            {"role": "user", "content": final_input, "time": now}
        )
        st.session_state.msg_count += 1

        conversation_history = st.session_state.messages[:-1]
        if not is_within_limit(conversation_history):
            conversation_history = truncate_messages(conversation_history)
            st.session_state.messages = (
                conversation_history
                + [st.session_state.messages[-1]]
            )

        # v3 RAG: retrieve relevant chunks before calling LLM
        retrieved_chunks = []
        if st.session_state.doc_chunks:
            from services.chunker import Chunk
            chunks = [
                Chunk(content=c["content"], source_filename=c["source"], chunk_index=c["index"])
                for c in st.session_state.doc_chunks
            ]
            retrieved = retrieve(final_input, chunks, top_k=3)
            retrieved_chunks = retrieved
            st.session_state.last_retrieved = [
                {"content": r.content, "score": r.score, "source": r.source_filename, "index": r.chunk_index}
                for r in retrieved
            ]

        with st.spinner(""):
            reply = call_llama(
                user_msg=final_input,
                personality_key=st.session_state.personality,
                user_name=st.session_state.user_name,
                topics=st.session_state.topics_discussed,
                conversation_history=st.session_state.messages[:-1],
                current_context=st.session_state.current_context,
                last_question=st.session_state.last_question,
                last_answer=st.session_state.last_answer,
                retrieved_chunks=retrieved_chunks,
            )

        st.session_state.messages.append(
            {"role": "assistant", "content": reply, "time": datetime.now().strftime("%H:%M")}
        )

        if is_quiz_request(final_input):
            st.session_state.current_context = "quiz"
            st.session_state.last_question = final_input[:200]
            st.session_state.last_answer = extract_answer_from_response(reply)

        intent = detect_intent(final_input.lower())
        if intent in ("give_answer", "give_explanation") and st.session_state.last_question:
            if intent == "give_answer":
                st.session_state.last_answer = reply[:500]

        save_session("default", dict(st.session_state))
        st.rerun()