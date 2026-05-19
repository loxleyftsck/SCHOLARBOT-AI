import time
import importlib
import sys



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
# NOTE: st.markdown() MUST be called before any st.button() / st.chat_input()
# calls in this file. Streamlit mounts widget DOM in call order; injecting CSS
# first ensures widget styles are overridden before the browser paints them.
from ui.styles import CSS
try:
    from ui.icons import ICONS
except ModuleNotFoundError:
    try:
        from scholarbot.ui.icons import ICONS
    except ModuleNotFoundError:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui"))
        from icons import ICONS
st.markdown(CSS, unsafe_allow_html=True)

# ─── Core Imports ─────────────────────────────────────────────────────────────
from core import (
    call_llama,
    stream_chat,
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
    build_system_prompt,
)
from core.memory_manager import reset_rag_docs
from prompts import PERSONALITIES, MODES, MODE_PLACEHOLDERS

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



# ─── Session State Init ───────────────────────────────────────────────────────
defaults = init_defaults()
defaults["session_start"] = "init"
defaults["chip_input"] = None
defaults["rag_error"] = None  # v3: upload error message
defaults["rag_processing"] = False  # v3: processing indicator
defaults["use_react_chat"] = True  # Enable React chat component
defaults["enable_streaming"] = True  # Enable streaming responses
for key, default_val in defaults.items():
    if key == "session_start":
        from datetime import datetime
        st.session_state.setdefault(key, datetime.now().strftime("%H:%M"))
    else:
        st.session_state.setdefault(key, default_val)

# ─── Callbacks ─────────────────────────────────────────────────────────────────

def _reset_chat_callback():
    """Safe reset: clears conversation, keeps profile + RAG documents."""
    print("[RESET] state cleared")
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
    """Clear all uploaded RAG documents from session state.

    MUST directly mutate st.session_state — reset_rag_docs() returns a new dict.
    """
    st.session_state.uploaded_docs = []
    st.session_state.doc_texts = []
    st.session_state.doc_chunks = []
    st.session_state.last_retrieved = []
    st.session_state.rag_error = None


def _process_user_message(input_text: str):
    """Shared message processing for both chat input and chip clicks.

    Extracts to a single function to prevent duplicate logic drift.
    Steps: validate → extract topic → append message → check token limit →
           RAG retrieval → LLM call (streaming or non-streaming) → append reply → detect context → save → rerun.
    """
    from datetime import datetime
    from services.chunker import Chunk

    if not is_safe_message(input_text):
        validation = validate_message(input_text)
        st.error(validation.message)
        return

    topic = extract_topic(input_text)
    if topic and topic not in st.session_state.topics_discussed:
        st.session_state.topics_discussed.append(topic)

    now = datetime.now().strftime("%H:%M")
    user_msg_id = f"user-{len(st.session_state.messages)}"
    st.session_state.messages.append(
        {"role": "user", "content": input_text, "time": now, "id": user_msg_id}
    )
    st.session_state.msg_count += 1

    conversation_history = st.session_state.messages[:-1]
    if not is_within_limit(conversation_history):
        conversation_history = truncate_messages(conversation_history)
        st.session_state.messages = (
            conversation_history + [st.session_state.messages[-1]]
        )

    # v3 RAG: retrieve relevant chunks before calling LLM
    retrieved_chunks = []
    if st.session_state.doc_chunks:
        chunks = [
            Chunk(content=c["content"], source_filename=c["source"], chunk_index=c["index"])
            for c in st.session_state.doc_chunks
        ]
        retrieved = retrieve(input_text, chunks, top_k=3)
        retrieved_chunks = retrieved
        st.session_state.last_retrieved = [
            {"content": r.content, "score": r.score, "source": r.source_filename, "index": r.chunk_index}
            for r in retrieved
        ]

    # Build messages for LLM
    from core.rag_context import build_rag_system_prompt, should_use_rag

    base_system_prompt = build_system_prompt(
        personality_key=st.session_state.personality,
        user_name=st.session_state.user_name,
        topics=st.session_state.topics_discussed,
        current_context=st.session_state.current_context,
        last_question=st.session_state.last_question,
    )

    # Inject RAG context if available
    has_documents = bool(retrieved_chunks)
    if retrieved_chunks and should_use_rag(input_text, has_documents=has_documents):
        system_content = build_rag_system_prompt(base_system_prompt, retrieved_chunks, st.session_state.current_context)
    else:
        system_content = base_system_prompt

    messages = [{"role": "system", "content": system_content}]
    for m in st.session_state.messages[:-1]:
        role = "user" if m["role"] == "user" else "assistant"
        messages.append({"role": role, "content": m["content"]})
    messages.append({"role": "user", "content": input_text})

    # Streaming or non-streaming based on settings
    if st.session_state.get("enable_streaming", True) and st.session_state.get("use_react_chat", True):
        # STREAMING MODE with React component
        import uuid
        streaming_msg_id = f"assistant-{uuid.uuid4().hex[:12]}"

        # Create placeholder for streaming message
        st.session_state.messages.append({
            "role": "assistant",
            "content": "",
            "time": datetime.now().strftime("%H:%M"),
            "id": streaming_msg_id,
        })

        # Render React component with typing indicator
        streaming_placeholder = st.empty()
        with streaming_placeholder.container():
            render_chat_html(
                messages=st.session_state.messages,
                is_typing=True,
                height=600,
                key="chat_main_typing",
            )

        accumulated_text = ""
        last_render_time = 0
        try:
            for token in stream_chat(messages=messages):
                accumulated_text += token

                # Update the last message content
                st.session_state.messages[-1]["content"] = accumulated_text

                # Throttle React component updates to prevent UI lag on high-speed APIs like Groq
                current_time = time.time()
                if current_time - last_render_time > 0.06:
                    with streaming_placeholder.container():
                        render_chat_html(
                            messages=st.session_state.messages,
                            streaming_message_id=streaming_msg_id,
                            height=600,
                            key="chat_main",
                        )
                    last_render_time = current_time

            # Final render to ensure the complete text is displayed
            with streaming_placeholder.container():
                render_chat_html(
                    messages=st.session_state.messages,
                    streaming_message_id=streaming_msg_id,
                    height=600,
                    key="chat_main",
                )

        except Exception as e:
            accumulated_text = f"Error during streaming: {str(e)}"
            st.session_state.messages[-1]["content"] = accumulated_text

        # Finalize - update timestamp
        st.session_state.messages[-1]["time"] = datetime.now().strftime("%H:%M")
        reply = accumulated_text

    else:
        # NON-STREAMING MODE (fallback)
        with st.spinner(""):
            reply = call_llama(
                user_msg=input_text,
                personality_key=st.session_state.personality,
                user_name=st.session_state.user_name,
                topics=st.session_state.topics_discussed,
                conversation_history=st.session_state.messages[:-1],
                current_context=st.session_state.current_context,
                last_question=st.session_state.last_question,
                last_answer=st.session_state.last_answer,
                retrieved_chunks=retrieved_chunks,
            )

        assistant_msg_id = f"assistant-{len(st.session_state.messages)}"
        st.session_state.messages.append(
            {"role": "assistant", "content": reply, "time": datetime.now().strftime("%H:%M"), "id": assistant_msg_id}
        )

    if is_quiz_request(input_text):
        st.session_state.current_context = "quiz"
        st.session_state.last_question = input_text[:200]
        st.session_state.last_answer = extract_answer_from_response(reply)

    intent = detect_intent(input_text.lower())
    if intent in ("give_answer", "give_explanation") and st.session_state.last_question:
        if intent == "give_answer":
            st.session_state.last_answer = reply[:500]

    save_session("default", dict(st.session_state))
    st.rerun()


# ─── UI Imports ───────────────────────────────────────────────────────────────
from ui.sidebar import (
    HEADER_HTML,
    SECTION_LABELS,
    GROQ_KEY_HELP,
    GROQ_KEY_PH,
    NAME_PLACEHOLDER,
    CHAT_PLACEHOLDER_DEFAULT,
    memory_card_html,
)
from ui import (
    render_chat_html,
    get_or_create_manager,
    StreamingManager,
)

# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo + Wordmark
    st.markdown(HEADER_HTML.replace("\n", " ").strip(), unsafe_allow_html=True)

    # Profile Mini Card (compact: avatar + greeting + personality)
    greeting = f"Halo, {st.session_state.user_name}" if st.session_state.user_name else "Halo!"
    profile_html = f'''<div class="profile-mini-card">
<div class="profile-avatar">{st.session_state.user_name[0].upper() if st.session_state.user_name else "S"}</div>
<div class="profile-info">
<div class="profile-greeting">{greeting}</div>
<div class="profile-subtext">Semangat belajar hari ini!</div>
</div>
</div>'''
    st.markdown(profile_html.replace("\n", " ").strip(), unsafe_allow_html=True)

    # Personality Selector (compact, no label)
    st.markdown('<div class="sidebar-section-title">Personality AI</div>', unsafe_allow_html=True)
    persona_keys = list(PERSONALITIES.keys())
    try:
        persona_index = persona_keys.index(st.session_state.personality)
    except ValueError:
        persona_index = 0
    persona = st.selectbox(
        "Personality",
        persona_keys,
        index=persona_index,
        label_visibility="collapsed",
        key="personality_selector"
    )
    if persona != st.session_state.personality:
        st.session_state.personality = persona

    # Menu Items (Core Actions)
    st.markdown('<div class="sidebar-section-title">Menu Utama</div>', unsafe_allow_html=True)

    # Belajar (default mode)
    if st.button("Belajar", key="menu_belajar", use_container_width=True):
        st.session_state.active_mode = None  # Default mode

    # Rangkuman
    if st.button("Rangkuman", key="menu_rangkuman", use_container_width=True):
        st.session_state.active_mode = "✍️ Rangkum Materi"

    # Latihan Soal
    if st.button("Latihan Soal", key="menu_latihan", use_container_width=True):
        st.session_state.active_mode = "🧪 Quiz Generator"

    # Mind Map
    if st.button("Mind Map", key="menu_mindmap", use_container_width=True):
        st.session_state.active_mode = "🗺️ Mind Map"

    st.markdown('<div class="sidebar-section-title">Penyimpanan</div>', unsafe_allow_html=True)

    # Riwayat (placeholder for future feature)
    if st.button("Riwayat", key="menu_riwayat", use_container_width=True):
        pass  # TODO: Implement history view

    # Reset Chat
    if st.button("Reset Chat", key="menu_reset", use_container_width=True):
        _reset_chat_callback()
        st.rerun()

    # Upload Button
    st.markdown('<div class="sidebar-menu-item menu-upload-btn">', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload Materi",
        type=["txt", "pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="Upload materi belajar (.txt atau .pdf)",
        key="file_uploader"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Process uploaded files
    if uploaded_files:
        st.session_state.rag_error = None
        existing_names = {d["filename"] for d in st.session_state.uploaded_docs}

        for file in uploaded_files:
            fname = file.name
            if fname in existing_names:
                continue

            try:
                file_bytes = file.getvalue()
                file_ext = get_file_extension(fname)
                text = extract_document(file_bytes, fname, file_ext)
                chunks = chunk_text(text, strategy="auto", filename=fname)
                info = get_document_info(text, fname)

                doc_meta = {
                    "filename": fname,
                    "size": len(file_bytes),
                    "type": file_ext,
                    "char_count": info["char_count"],
                    "chunk_count": len(chunks),
                }
                st.session_state.uploaded_docs.append(doc_meta)
                st.session_state.doc_texts.append(text)

                for chunk in chunks:
                    st.session_state.doc_chunks.append({
                        "content": chunk.content,
                        "source": chunk.source_filename,
                        "index": chunk.chunk_index,
                    })
            except ValueError as e:
                st.session_state.rag_error = str(e)

    # Upload status
    if st.session_state.rag_error:
        st.error(st.session_state.rag_error)
        st.session_state.rag_error = None
    elif st.session_state.uploaded_docs:
        doc_count = len(st.session_state.uploaded_docs)
        st.markdown(f'<div class="upload-status-box">{doc_count} dokumen aktif</div>', unsafe_allow_html=True)
        if st.button("Hapus Semua", key="clear_docs_btn", use_container_width=True):
            _clear_docs_callback()

    # Premium Upgrade Card at bottom
    pro_html = f'''<div class="pro-card">
<div class="pro-header">
<div class="pro-icon">{ICONS["crown"]}</div>
<div class="pro-title">Upgrade ke ScholarPro</div>
</div>
<div class="pro-desc">Akses fitur premium tanpa batas.</div>
<div class="pro-btn">Upgrade Sekarang</div>
</div>'''
    st.markdown(pro_html.replace("\n", " ").strip(), unsafe_allow_html=True)

# ─── MAIN AREA ──────────────────────────────────────────────────────────────────

# ─── Welcome Screen ────────────────────────────────────────────────────────────
if not st.session_state.messages:
    # ─── Render Native Welcome Screen ───
    from ui.welcome import render_native_welcome
    render_native_welcome(user_name=st.session_state.user_name)




# ─── Render Chat History ────────────────────────────────────────────────────────
if st.session_state.messages:
    if st.session_state.get("use_react_chat", True):
        # React component rendering
        render_chat_html(
            messages=st.session_state.messages,
            is_typing=False,
            height=600,
            key="chat_main",
        )
    else:
        # Fallback HTML rendering
        for msg in st.session_state.messages:
            is_user = msg["role"] == "user"
            row_cls = "user" if is_user else "bot"
            bubble_cls = "user" if is_user else "bot"
            st.markdown(f"""
            <div class="msg-row {row_cls}">
                <div class="avatar {row_cls}">{'U' if is_user else 'S'}</div>
                <div>
                    <div class="bubble {bubble_cls}">{msg["content"]}</div>
                    <div class="msg-time">{msg.get("time", "")}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ─── Chat Input ─────────────────────────────────────────────────────────────────
active_mode = st.session_state.get("active_mode")
placeholder_text = MODE_PLACEHOLDERS.get(active_mode, "") if active_mode else ""
placeholder = placeholder_text or CHAT_PLACEHOLDER_DEFAULT

user_input = st.chat_input(placeholder=placeholder)

if user_input:
    final_input = user_input
    if active_mode:
        mode_text = MODES[active_mode]
        if not user_input.startswith(mode_text):
            final_input = mode_text + " " + user_input
        st.session_state.active_mode = None

    _process_user_message(final_input)