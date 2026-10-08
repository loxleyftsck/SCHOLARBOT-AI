"""FastAPI Backend Server for ScholarBot.

Bridges the ScholarBot AI Core & RAG services to any custom SPA frontend (React/Next.js).
Reuses 100% of core/ llm_client, session_helpers, prompts, and services.
"""

import os
import sys
import uuid
import json
import time
import math
from collections import deque
from typing import List, Dict, Any, Optional
from datetime import datetime

# Load .env before anything else
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

# Add workspace directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.llm_client import stream_chat, chat, DEFAULT_MODEL
from core.session_helpers import (
    build_system_prompt,
    detect_intent,
    expand_short_command,
    is_quiz_request,
    extract_answer_from_response,
    extract_topic
)
from core.rag_context import (
    build_rag_system_prompt,
    should_use_rag,
    build_citation_map,
    extract_citation_ids
)
from services.document_loader import get_document_info
from services.chunker import chunk_text
from services.retriever import RetrievedChunk, select_context_chunks
from services.semantic_search import hybrid_retrieve as retrieve
from storage.json_store import load_session, save_session
from storage import shared_store
from starlette.concurrency import run_in_threadpool

# Initialize FastAPI App
app = FastAPI(
    title="ScholarBot API",
    description="High-performance backend API for the ScholarBot learning workspace",
    version="1.0.0"
)

# Configure CORS dynamically based on environment with fallback to safe local development ports
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_raw:
    allowed_origins = [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:4175"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RAG-Sources", "X-Retrieval-Status", "Retry-After"],
)

# Vercel must use shared state, never instance-local files or request counters.
SESSION_BACKEND = os.getenv("SESSION_BACKEND", "supabase" if os.getenv("VERCEL") else "local")
if os.getenv("VERCEL") and SESSION_BACKEND != "supabase":
    raise RuntimeError("Vercel requires shared session storage.")
SHARED_STORAGE = SESSION_BACKEND == "supabase"

# Local single-worker quota; shared deployments use an atomic database RPC.
DEMO_REQUESTS_PER_MINUTE = int(os.getenv("DEMO_REQUESTS_PER_MINUTE", "0"))
DEMO_REQUESTS_PER_DAY = int(os.getenv("DEMO_REQUESTS_PER_DAY", "0"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", "5242880"))
DEMO_REQUEST_TIMES = deque()
DEMO_DAILY_REQUEST_TIMES = deque()

def demo_error_response(request, status, detail, retry_after=None):
    headers = {"Retry-After": str(retry_after)} if retry_after else {}
    response = JSONResponse(status_code=status, content={"detail": detail}, headers=headers)
    origin = request.headers.get("origin")
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "Retry-After"
        response.headers["Vary"] = "Origin"
    return response

@app.middleware("http")
async def limit_demo_requests(request, call_next):
    limited = request.method == "POST" or (request.method == "GET" and request.url.path == "/api/quiz")
    if limited and (DEMO_REQUESTS_PER_MINUTE > 0 or DEMO_REQUESTS_PER_DAY > 0):
        retry_after = 0
        if SHARED_STORAGE:
            try:
                retry_after = await run_in_threadpool(shared_store.quota, DEMO_REQUESTS_PER_MINUTE, DEMO_REQUESTS_PER_DAY)
            except HTTPException as exc:
                return demo_error_response(request, exc.status_code, exc.detail)
        else:
            now = time.monotonic()
            for queue, window in ((DEMO_REQUEST_TIMES, 60), (DEMO_DAILY_REQUEST_TIMES, 86400)):
                while queue and now - queue[0] >= window:
                    queue.popleft()
            for queue, window, limit in ((DEMO_REQUEST_TIMES, 60, DEMO_REQUESTS_PER_MINUTE), (DEMO_DAILY_REQUEST_TIMES, 86400, DEMO_REQUESTS_PER_DAY)):
                if limit > 0 and len(queue) >= limit:
                    retry_after = max(retry_after, max(1, math.ceil(window - (now - queue[0]))))
        if retry_after:
            detail = "Kuota demo hari ini habis. Coba lagi nanti." if retry_after > 60 else "Demo sedang ramai. Coba lagi dalam satu menit."
            return demo_error_response(request, 429, detail, retry_after)
        if not SHARED_STORAGE and DEMO_REQUESTS_PER_MINUTE > 0:
            DEMO_REQUEST_TIMES.append(now)
        if not SHARED_STORAGE and DEMO_REQUESTS_PER_DAY > 0:
            DEMO_DAILY_REQUEST_TIMES.append(now)
    return await call_next(request)

# Global session database in memory (perfect for local development)
class SessionState:
    def __init__(self):
        self.messages: List[Dict[str, str]] = []
        self.topics_discussed: List[str] = []
        self.current_context: str = ""
        self.active_mode: str = "belajar"
        self.last_question: str = ""
        self.last_answer: str = ""
        self.uploaded_docs: List[Dict[str, Any]] = []
        self.doc_chunks: List[Any] = []
        self.quiz_scores: List[Dict[str, Any]] = []  # track scores history
        self.created_at: datetime = datetime.now()
        self.revision: int = 0

SESSIONS: Dict[str, SessionState] = {}


def get_or_create_session(session_id: Optional[str]) -> tuple[str, SessionState]:
    """Retrieve or initialize a chat session, restoring from JSON disk storage if present."""
    if not session_id or session_id.strip() == "":
        session_id = str(uuid.uuid4())
    
    if len(session_id) > 128:
        raise HTTPException(400, "ID sesi tidak valid.")
    if SHARED_STORAGE:
        # Always read authoritative storage; do not reuse an instance's cached state.
        saved = shared_store.load(session_id)
        state = SessionState()
        if saved:
            payload = saved["payload"]
            for field in ("messages", "topics_discussed", "uploaded_docs", "quiz_scores",
                          "current_context", "active_mode", "last_question", "last_answer"):
                if field in payload:
                    setattr(state, field, payload[field])
            from services.chunker import Chunk
            state.doc_chunks = [Chunk(**c) for c in payload.get("doc_chunks", [])]
            state.revision = saved["revision"]
        return session_id, state

    if session_id not in SESSIONS:
        # Try to load from disk JSON storage
        saved = load_session(session_id)
        state = SessionState()
        if saved:
            state.messages = saved.get("messages", [])
            state.topics_discussed = saved.get("topics_discussed", [])
            state.uploaded_docs = saved.get("uploaded_docs", [])
            state.doc_chunks = saved.get("doc_chunks", [])
            state.quiz_scores = saved.get("quiz_scores", [])
            print(f"[DISK LOAD] Restored session {session_id} successfully.")
        SESSIONS[session_id] = state
        
    return session_id, SESSIONS[session_id]


def persist_session(session_id: str, state: SessionState):
    """Persist session details to disk safely."""
    if SHARED_STORAGE:
        from dataclasses import asdict
        payload = {field: getattr(state, field) for field in (
            "messages", "topics_discussed", "uploaded_docs", "quiz_scores", "current_context",
            "active_mode", "last_question", "last_answer")}
        payload["messages"] = payload["messages"][-60:]
        payload["quiz_scores"] = payload["quiz_scores"][-100:]
        payload["topics_discussed"] = payload["topics_discussed"][-50:]
        payload["doc_chunks"] = [asdict(c) if hasattr(c, "content") else c for c in state.doc_chunks]
        if len(json.dumps(payload).encode("utf-8")) > 2000000:
            raise HTTPException(413, "Sesi demo terlalu besar. Hapus dokumen atau mulai sesi baru.")
        state.revision = shared_store.save(session_id, payload, state.revision)
        return
    try:
        state_dict = {
            "messages": state.messages,
            "user_name": "Budi",
            "personality": "😊 Santai & Friendly",
            "topics_discussed": state.topics_discussed,
            "msg_count": len(state.messages),
            "session_start": state.created_at.strftime("%H:%M"),
            "uploaded_docs": state.uploaded_docs,
            "doc_chunks": state.doc_chunks,
            "quiz_scores": state.quiz_scores
        }
        save_session(session_id, state_dict)
    except Exception as e:
        print(f"[Disk Save Error] Gagal menyimpan sesi {session_id}: {e}")


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    personality: str = "😊 Santai & Friendly"
    user_name: str = "Budi"
    mode: str = "belajar"  # 'belajar', 'rangkuman', 'latihan', 'mindmap'


class QuizSubmitRequest(BaseModel):
    session_id: str
    topic: str
    is_correct: bool


class MindMapRequest(BaseModel):
    topic: str
    session_id: Optional[str] = None


class MindMapExpandRequest(BaseModel):
    topic: str
    node_id: str
    node_label: str
    existing_nodes: List[Dict[str, Any]]
    existing_edges: List[Dict[str, Any]]
    session_id: Optional[str] = None



# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    if SHARED_STORAGE:
        shared_store.load("__healthcheck__")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
        "session_backend": SESSION_BACKEND
    }


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Chat endpoint supporting both streaming and clean contextual responses."""
    session_id, state = get_or_create_session(req.session_id)
    user_msg = req.message.strip()

    if SHARED_STORAGE and len(user_msg) > 8000:
        raise HTTPException(413, "Pesan demo maksimal 8000 karakter.")
    if not user_msg:
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong")

    # Update session personality
    personality_key = req.personality

    previous_mode = state.active_mode
    state.active_mode = req.mode

    # Auto-detect quiz or mindmap mode
    if req.mode == "latihan" or is_quiz_request(user_msg):
        state.current_context = "quiz"
    elif req.mode == "mindmap":
        state.current_context = "mindmap"

    elif req.mode == previous_mode and state.current_context == "quiz" and detect_intent(user_msg):
        pass  # Keep an in-chat quiz follow-up, but never carry it across mode switches.
    else:
        state.current_context = "summary" if req.mode == "rangkuman" else ""
        state.last_question = ""
        state.last_answer = ""

    # Extract topic for memory card tracking
    extracted_topic = extract_topic(user_msg)
    if extracted_topic and extracted_topic not in state.topics_discussed:
        state.topics_discussed.append(extracted_topic)

    # Check for short follow-up command intent and expand context (BUG-07)
    intent = detect_intent(user_msg) if (state.current_context == "quiz" or bool(state.last_question)) else None
    if intent:
        effective_msg = expand_short_command(
            user_msg, state.last_question, state.last_answer, state.current_context
        )
    else:
        effective_msg = user_msg

    # Build prompt with RAG if documents are uploaded and query is relevant
    has_documents = bool(state.doc_chunks)
    retrieved_chunks = []
    retrieval_status = {"method": "not_run", "fallback": False}
    
    retrieval_query = effective_msg
    if effective_msg == user_msg and user_msg.lower() in {"lanjut", "hint", "jelaskan", "bahas", "buat lagi"}:
        previous_query = next((m["content"] for m in reversed(state.messages) if m["role"] == "user"), "")
        if previous_query:
            retrieval_query = f"{previous_query}\nPertanyaan lanjutan: {user_msg}"
    use_rag = should_use_rag(effective_msg, has_documents)
    if use_rag:
        # Retrieve evidence for the effective follow-up question, not its short command.
        try:
            retrieved_chunks = select_context_chunks(retrieve(retrieval_query, state.doc_chunks, top_k=3))
            from services.semantic_search import get_retrieval_status
            retrieval_status = get_retrieval_status()
        except Exception as e:
            retrieval_status = {"method": "failed", "fallback": False}
            print(f"[RAG Error] Gagal melakukan retrieve: {e}")

    # Build system prompt
    base_system_prompt = build_system_prompt(
        personality_key=personality_key,
        user_name=req.user_name,
        topics=state.topics_discussed,
        current_context=state.current_context,
        last_question=state.last_question
    )

    if retrieved_chunks:
        system_content = build_rag_system_prompt(
            base_system_prompt, retrieved_chunks, state.current_context
        )
    else:
        system_content = base_system_prompt

    if use_rag and not retrieved_chunks:
        system_content += "\nMateri diunggah, tetapi tidak ditemukan potongan yang relevan. Nyatakan sumber belum cukup; jangan mengarang sitasi."
    if req.mode == "rangkuman":
        system_content += "\nBuat rangkuman terstruktur: pokok bahasan, konsep penting, dan batas cakupan. Jangan mengklaim merangkum seluruh dokumen bila hanya sebagian konteks tersedia."

    # Build standard messages list
    messages = [{"role": "system", "content": system_content}]
    # Conservative character budget for history, not an exact model tokenizer.
    history = []
    remaining_chars = 16000
    for m in reversed(state.messages):
        content = m["content"]
        if len(content) > remaining_chars:
            break
        history.append({"role": "user" if m["role"] == "user" else "assistant", "content": content})
        remaining_chars -= len(content)
    history.reverse()
    while history and history[0]["role"] != "user":
        history.pop(0)
    messages.extend(history)
    messages.append({"role": "user", "content": effective_msg})

    # Save user message to history
    user_msg_time = datetime.now().strftime("%H:%M")
    state.messages.append({
        "id": f"user-{uuid.uuid4().hex[:8]}",
        "role": "user",
        "content": user_msg,
        "time": user_msg_time
    })
    persist_session(session_id, state)

    # Serialize retrieved chunks as numbered citations ([1], [2], ...) for the frontend
    serialized_chunks = []
    if retrieved_chunks:
        serialized_chunks = build_citation_map(retrieved_chunks, snippet_chars=0)

    max_citation_id = len(serialized_chunks)

    # Generator for streaming tokens
    def token_generator():
        accumulated_text = ""
        try:
            for token in stream_chat(messages=messages):
                accumulated_text += token
                yield token

            # Post-processing after stream is complete
            bot_msg_time = datetime.now().strftime("%H:%M")
            state.messages.append({
                "id": f"bot-{uuid.uuid4().hex[:8]}",
                "role": "assistant",
                "content": accumulated_text,
                "time": bot_msg_time,
                "sources": serialized_chunks,
                "retrieval_status": retrieval_status,
                "cited_ids": extract_citation_ids(accumulated_text, max_id=max_citation_id)
            })
            
            # Cache answers if quiz context
            if state.current_context == "quiz":
                state.last_question = user_msg
                state.last_answer = extract_answer_from_response(accumulated_text)

            persist_session(session_id, state)

        except HTTPException:
            yield "\n\n[Sesi belum tersimpan. Muat ulang sebelum mengirim ulang pesan.]"
            return
        except Exception as e:
            err_msg = f"\nError streaming response: {str(e)}"
            # If an error happens mid-stream, save a valid assistant message to history to keep roles alternating (BUG-01)
            bot_msg_time = datetime.now().strftime("%H:%M")
            final_content = (accumulated_text + f"\n\n[Koneksi terputus: {str(e)}]") if accumulated_text else "Maaf, terjadi kesalahan koneksi saat menerima respons. Silakan kirim ulang pesan Anda."
            state.messages.append({
                "id": f"bot-{uuid.uuid4().hex[:8]}",
                "role": "assistant",
                "content": final_content,
                "time": bot_msg_time,
                "sources": serialized_chunks,
                "retrieval_status": retrieval_status,
                "cited_ids": extract_citation_ids(final_content, max_id=max_citation_id)
            })
            persist_session(session_id, state)
            yield err_msg

    headers = {
        "X-Retrieval-Status": json.dumps(retrieval_status),
        "Access-Control-Expose-Headers": "X-RAG-Sources, X-Retrieval-Status",
        "X-RAG-Sources": json.dumps(serialized_chunks, ensure_ascii=False)
    }
    return StreamingResponse(token_generator(), media_type="text/plain", headers=headers)


@app.post("/api/upload")
async def upload_document(
    session_id: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    """RAG Document Upload Endpoint."""
    session_id, state = get_or_create_session(session_id)
    
    if SHARED_STORAGE and len(state.uploaded_docs) >= 5:
        raise HTTPException(413, "Demo maksimal 5 dokumen per sesi. Hapus dokumen terlebih dahulu.")
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in (".txt", ".pdf"):
        raise HTTPException(status_code=400, detail="Hanya mendukung file .txt atau .pdf")

    # Read file content safely
    try:
        content_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"Ukuran dokumen maksimal {MAX_UPLOAD_BYTES // (1024 * 1024)} MB untuk demo.")
        
        from services.document_loader import extract_document
        try:
            raw_text = extract_document(content_bytes, file.filename, file_extension[1:])
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="File kosong atau tidak dapat diekstrak")

        if SHARED_STORAGE and len(raw_text) > 100000:
            raise HTTPException(413, "Teks hasil ekstraksi maksimal 100000 karakter untuk demo.")
        # Chunk the extracted text
        new_chunks = chunk_text(raw_text, filename=file.filename)
        
        # Save to session chunks
        state.doc_chunks.extend(new_chunks)
        
        # Save metadata with text preview
        state.uploaded_docs.append({
            "filename": file.filename,
            "size": f"{(len(content_bytes) / 1024):.1f} KB",
            "type": file_extension[1:].upper(),
            "preview": raw_text[:800] if len(raw_text) > 800 else raw_text
        })
        persist_session(session_id, state)

        return {
            "message": "Dokumen berhasil diunggah dan diproses!",
            "session_id": session_id,
            "filename": file.filename,
            "chunks_count": len(new_chunks),
            "uploaded_docs": state.uploaded_docs
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses dokumen: {str(e)}")


@app.get("/api/session/{session_id}")
async def get_session_details(session_id: str):
    """Retrieve full details of a session (messages, topics, docs)."""
    session_id, state = get_or_create_session(session_id)
    return {
        "session_id": session_id,
        "messages": state.messages,
        "topics_discussed": state.topics_discussed,
        "current_context": state.current_context,
        "uploaded_docs": state.uploaded_docs,
        "doc_chunks_count": len(state.doc_chunks)
    }


@app.post("/api/session/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset a chat session history while keeping uploaded documents."""
    session_id, state = get_or_create_session(session_id)
    state.messages = []
    state.topics_discussed = []
    state.current_context = ""
    state.last_question = ""
    state.last_answer = ""
    persist_session(session_id, state)
    
    return {"message": "Sesi obrolan berhasil dibersihkan", "session_id": session_id}


class FeedbackRequest(BaseModel):
    message_id: str
    feedback: str  # "like", "dislike", "neutral"


@app.post("/api/session/{session_id}/message/feedback")
async def message_feedback(session_id: str, req: FeedbackRequest):
    """Save user feedback (like/dislike) for a specific message in the session history."""
    session_id, state = get_or_create_session(session_id)
    for m in state.messages:
        if m.get("id") == req.message_id:
            m["feedback"] = req.feedback
            persist_session(session_id, state)
            return {"status": "success", "message_id": req.message_id, "feedback": req.feedback}
    raise HTTPException(status_code=404, detail="Pesan tidak ditemukan")


@app.post("/api/session/{session_id}/clear-docs")
async def clear_docs(session_id: str):
    """Clear all uploaded documents for a session."""
    session_id, state = get_or_create_session(session_id)
    state.uploaded_docs = []
    state.doc_chunks = []
    persist_session(session_id, state)
    
    return {"message": "Semua dokumen berhasil dihapus", "session_id": session_id}


@app.get("/api/session/{session_id}/search-doc")
async def search_doc(session_id: str, query: str = Query(...), filename: str = Query(...)):
    """Search for matching chunks within a specific document in the session using semantic/keyword retrieval."""
    session_id, state = get_or_create_session(session_id)
    from services.chunker import Chunk
    from services.semantic_search import get_retrieval_status
    doc_chunks = []
    for c in state.doc_chunks:
        source = c.source_filename if hasattr(c, "source_filename") else c.get("source_filename", c.get("source", ""))
        if source != filename:
            continue
        doc_chunks.append(c if isinstance(c, Chunk) else Chunk(c.get("content", ""), c.get("chunk_index", 0), source))
    found = retrieve(query, doc_chunks, top_k=5) if query and filename and doc_chunks else []
    status = get_retrieval_status() if query and filename and doc_chunks else {"method": "not_run", "fallback": False}
    persist_session(session_id, state)
    return {"results": [{"content": c.content, "chunk_index": c.chunk_index, "score": c.score} for c in found], "session_id": session_id, "retrieval_status": status}


@app.delete("/api/session/{session_id}/doc/{filename}")
async def delete_individual_document(session_id: str, filename: str):
    """Delete an individual uploaded document and its chunks from the session."""
    session_id, state = get_or_create_session(session_id)
    
    # Filter out the document from uploaded_docs
    initial_docs_count = len(state.uploaded_docs)
    state.uploaded_docs = [doc for doc in state.uploaded_docs if doc["filename"] != filename]
    
    if len(state.uploaded_docs) == initial_docs_count:
        raise HTTPException(status_code=404, detail=f"Dokumen {filename} tidak ditemukan")
        
    # Filter out chunks corresponding to this filename
    state.doc_chunks = [chunk for chunk in state.doc_chunks if 
                        (chunk.source_filename if hasattr(chunk, "source_filename") else chunk.get("source_filename", chunk.get("source", ""))) != filename]
    
    # Save the updated session state to disk
    persist_session(session_id, state)
    
    return {
        "message": f"Dokumen '{filename}' berhasil dihapus",
        "session_id": session_id,
        "uploaded_docs": state.uploaded_docs
    }


@app.get("/api/quiz")
async def generate_quiz_endpoint(session_id: Optional[str] = Query(None)):
    """Generate a dynamic multiple choice quiz based on the conversation history."""
    session_id, state = get_or_create_session(session_id)
    
    # Decide the topic based on history
    topic = "Machine Learning & AI"
    if state.topics_discussed:
        topic = state.topics_discussed[-1]
    elif len(state.messages) > 1:
        # Fallback: extract topic from last user message
        user_msgs = [m for m in state.messages if m["role"] == "user"]
        if user_msgs:
            extracted = extract_topic(user_msgs[-1]["content"])
            if extracted:
                topic = extracted

    # Prompt Groq to return strict JSON format
    prompt_messages = [
        {
            "role": "system",
            "content": (
                "Anda adalah mesin pembuat kuis edukasi otomatis. "
                "Tugas Anda adalah membuat 1 (satu) soal pilihan ganda (A, B, C, D) yang cerdas dan mendidik "
                "berdasarkan topik yang diberikan. "
                "Anda WAJIB memberikan respons dalam format JSON murni tanpa ada pembukaan, penjelasan, atau penutup. "
                "JSON harus memiliki skema berikut secara presisi:\n"
                "{\n"
                '  "question": "teks pertanyaan di sini",\n'
                '  "options": [\n'
                '    {"key": "A", "text": "pilihan A"},\n'
                '    {"key": "B", "text": "pilihan B"},\n'
                '    {"key": "C", "text": "pilihan C"},\n'
                '    {"key": "D", "text": "pilihan D"}\n'
                "  ],\n"
                '  "correct": "KUNCI JAWABAN YANG BENAR (HANYA HURUF A/B/C/D)"\n'
                "}"
            )
        },
        {
            "role": "user",
            "content": f"Buatkan kuis pilihan ganda interaktif tentang topik: {topic}"
        }
    ]

    try:
        response_text = chat(
            messages=prompt_messages,
            model=DEFAULT_MODEL
        )
        
        # Clean markdown wrappers if present
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        quiz_json = json.loads(clean_text)
        # Add topic back to JSON
        quiz_json["topic"] = topic
        return quiz_json
    except Exception as e:
        print(f"[Generation Error] {type(e).__name__}")
        raise HTTPException(status_code=503, detail="Kuis belum berhasil dibuat. Silakan coba lagi.") from e


@app.post("/api/quiz/submit")
async def submit_quiz_score(req: QuizSubmitRequest):
    """Record a user quiz answer and calculate accumulated statistics."""
    session_id, state = get_or_create_session(req.session_id)
    
    score_item = {
        "topic": req.topic,
        "score": 100 if req.is_correct else 0,
        "is_correct": req.is_correct,
        "timestamp": datetime.now().isoformat()
    }
    state.quiz_scores.append(score_item)
    
    # Calculate accumulated performance
    total_quizzes = len(state.quiz_scores)
    correct_quizzes = sum(1 for q in state.quiz_scores if q["is_correct"])
    accuracy = (correct_quizzes / total_quizzes * 100) if total_quizzes > 0 else 0.0
    persist_session(session_id, state)
    
    return {
        "message": "Skor kuis berhasil dicatat!",
        "total_quizzes": total_quizzes,
        "correct_answers": correct_quizzes,
        "accuracy": accuracy,
        "scores_history": state.quiz_scores
    }


@app.post("/api/mindmap/generate")
async def generate_mindmap_endpoint(req: MindMapRequest):
    """Generate a structured, dynamic mind map based on the requested topic."""
    session_id, state = get_or_create_session(req.session_id)
    topic = req.topic.strip()
    
    # Check if the requested topic is just a meta-command/intent
    is_meta = any(cmd in topic.lower() for cmd in ["mindmap", "mind map", "peta konsep", "buat jadi", "kuis", "soal", "latihan"])
    
    if not topic or is_meta:
        # Fallback to the last discussed academic topic
        topic = ""
        if state.topics_discussed:
            valid_topics = [t for t in state.topics_discussed if not any(cmd in t.lower() for cmd in ["mindmap", "mind map", "peta konsep", "buat jadi", "kuis", "soal", "latihan"])]
            if valid_topics:
                topic = valid_topics[-1]
        
        # If still empty, use a sensible default
        if not topic:
            topic = "Machine Learning"
            
    system_content = (
        "Anda adalah asisten akademik yang ahli membuat peta konsep (mind map) interaktif.\n"
        "Buatlah peta konsep terstruktur dalam format JSON untuk topik yang diminta.\n"
        "Gunakan bahasa Indonesia yang jelas, ringkas, dan profesional.\n"
        "Anda WAJIB memberikan respons dalam format JSON murni dengan tepat dua kunci utama: 'nodes' dan 'edges'.\n"
        "\n"
        "Skema JSON yang harus Anda ikuti secara presisi:\n"
        "{\n"
        '  "nodes": [\n'
        '    {"id": "1", "label": "Nama Topik Utama", "type": "root", "desc": "Penjelasan singkat topik utama (1 kalimat)."},\n'
        '    {"id": "2", "label": "Subtopik A", "type": "branch", "desc": "Penjelasan singkat subtopik A (1 kalimat)."},\n'
        '    {"id": "3", "label": "Subtopik B", "type": "branch", "desc": "Penjelasan singkat subtopik B (1 kalimat)."}\n'
        '  ],\n'
        '  "edges": [\n'
        '    {"source": "1", "target": "2"},\n'
        '    {"source": "1", "target": "3"}\n'
        '  ]\n'
        "}\n"
        "\n"
        "Ketentuan:\n"
        "1. Node 'root' harus merepresentasikan topik utama (buat tepat 1 root node).\n"
        "2. Buatlah 3-4 subtopik utama ('branch') yang langsung terhubung ke root.\n"
        "3. Untuk setiap subtopik utama, buatlah 2-3 sub-cabang ('sub-branch') yang terhubung dengannya jika relevan, atau Anda bisa membiarkannya memiliki 3-5 subtopik 'branch' saja agar layoutnya seimbang.\n"
        "4. ID node harus unik (misalnya '1', '2', '3' atau berupa string deskriptif singkat).\n"
        "5. Label node harus singkat (1-3 kata saja).\n"
        "6. Jangan sertakan teks penjelasan lain sebelum atau sesudah JSON."
    )
    
    prompt_messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": f"Buatkan peta konsep interaktif tentang topik: {topic}"}
    ]
    
    try:
        response_text = chat(
            messages=prompt_messages,
            model=DEFAULT_MODEL,
            json_mode=True
        )
        
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        mindmap_json = json.loads(clean_text)
        return mindmap_json
    except Exception as e:
        print(f"[Generation Error] {type(e).__name__}")
        raise HTTPException(status_code=503, detail="Peta konsep belum berhasil dibuat. Silakan coba lagi.") from e


@app.post("/api/mindmap/expand")
async def expand_mindmap_endpoint(req: MindMapExpandRequest):
    """Expand a specific node in an existing mind map by adding new child nodes."""
    session_id, state = get_or_create_session(req.session_id)
    
    system_content = (
        "Anda adalah asisten akademik yang ahli memperluas peta konsep (mind map) interaktif.\n"
        "Kami memiliki peta konsep tentang topik '{topic}' yang saat ini memiliki struktur berikut:\n"
        "Nodes saat ini: {existing_nodes}\n"
        "Edges saat ini: {existing_edges}\n"
        "\n"
        "Tugas Anda adalah memperluas node '{node_label}' (ID: '{node_id}') dengan menambahkan tepat 3 sub-konsep baru yang bercabang langsung dari node tersebut.\n"
        "Anda WAJIB memberikan respons dalam format JSON murni dengan tepat dua kunci utama: 'nodes' dan 'edges'.\n"
        "Kunci ini hanya boleh berisi node dan edge BARU yang ditambahkan, bukan node dan edge yang sudah ada.\n"
        "\n"
        "Skema JSON yang harus Anda ikuti secara presisi:\n"
        "{{\n"
        '  "nodes": [\n'
        '    {{"id": "id-baru-1", "label": "Sub-konsep Baru 1", "type": "sub-branch", "desc": "Penjelasan singkat sub-konsep 1 (1 kalimat)."}},\n'
        '    {{"id": "id-baru-2", "label": "Sub-konsep Baru 2", "type": "sub-branch", "desc": "Penjelasan singkat sub-konsep 2 (1 kalimat)."}}\n'
        '  ],\n'
        '  "edges": [\n'
        '    {{"source": "{node_id}", "target": "id-baru-1"}},\n'
        '    {{"source": "{node_id}", "target": "id-baru-2"}}\n'
        '  ]\n'
        "}}\n"
        "\n"
        "Ketentuan:\n"
        "1. ID node baru harus benar-benar unik dan tidak boleh sama dengan ID node yang sudah ada.\n"
        "2. Semua edge baru harus menghubungkan node '{node_id}' sebagai 'source' ke ID node baru sebagai 'target'.\n"
        "3. Gunakan bahasa Indonesia yang jelas, ringkas, dan profesional.\n"
        "4. Label node baru harus singkat (1-3 kata saja).\n"
        "5. Jangan sertakan teks penjelasan lain sebelum atau sesudah JSON."
    ).format(
        topic=req.topic,
        node_label=req.node_label,
        node_id=req.node_id,
        existing_nodes=json.dumps(req.existing_nodes, ensure_ascii=False),
        existing_edges=json.dumps(req.existing_edges, ensure_ascii=False)
    )
    
    prompt_messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": f"Perluas node '{req.node_label}' (ID: {req.node_id}) di peta konsep."}
    ]
    
    try:
        response_text = chat(
            messages=prompt_messages,
            model=DEFAULT_MODEL,
            json_mode=True
        )
        
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        expansion_json = json.loads(clean_text)
        return expansion_json
    except Exception as e:
        print(f"[Generation Error] {type(e).__name__}")
        raise HTTPException(status_code=503, detail="Subtopik belum berhasil dibuat. Silakan coba lagi.") from e


if __name__ == "__main__":

    import uvicorn
    uvicorn.run(
        "api:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True, 
        reload_dirs=["core", "services", "ui", "prompts"]
    )
