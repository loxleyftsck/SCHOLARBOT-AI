"""FastAPI Backend Server for ScholarBot.

Bridges the ScholarBot AI Core & RAG services to any custom SPA frontend (React/Next.js).
Reuses 100% of core/ llm_client, session_helpers, prompts, and services.
"""

import os
import sys
import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

# Load .env before anything else
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Add workspace directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.llm_client import stream_chat, chat
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
from services.retriever import RetrievedChunk
from services.semantic_search import hybrid_retrieve as retrieve
from storage.json_store import load_session, save_session

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
        "http://127.0.0.1:3001"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global session database in memory (perfect for local development)
class SessionState:
    def __init__(self):
        self.messages: List[Dict[str, str]] = []
        self.topics_discussed: List[str] = []
        self.current_context: str = ""
        self.last_question: str = ""
        self.last_answer: str = ""
        self.uploaded_docs: List[Dict[str, Any]] = []
        self.doc_chunks: List[Any] = []
        self.quiz_scores: List[Dict[str, Any]] = []  # track scores history
        self.created_at: datetime = datetime.now()

SESSIONS: Dict[str, SessionState] = {}


def get_or_create_session(session_id: Optional[str]) -> tuple[str, SessionState]:
    """Retrieve or initialize a chat session, restoring from JSON disk storage if present."""
    if not session_id or session_id.strip() == "":
        session_id = str(uuid.uuid4())
    
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
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "groq_configured": bool(os.getenv("GROQ_API_KEY"))
    }


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Chat endpoint supporting both streaming and clean contextual responses."""
    session_id, state = get_or_create_session(req.session_id)
    user_msg = req.message.strip()

    if not user_msg:
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong")

    # Update session personality
    personality_key = req.personality

    # Auto-detect quiz or mindmap mode
    if req.mode == "latihan" or is_quiz_request(user_msg):
        state.current_context = "quiz"
    elif req.mode == "mindmap":
        state.current_context = "mindmap"

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
    
    if has_documents:
        # Retrieve top 3 relevant chunks
        try:
            retrieved_chunks = retrieve(user_msg, state.doc_chunks, top_k=3)
        except Exception as e:
            print(f"[RAG Error] Gagal melakukan retrieve: {e}")

    # Build system prompt
    base_system_prompt = build_system_prompt(
        personality_key=personality_key,
        user_name=req.user_name,
        topics=state.topics_discussed,
        current_context=state.current_context,
        last_question=state.last_question
    )

    if retrieved_chunks and should_use_rag(user_msg, has_documents=has_documents):
        system_content = build_rag_system_prompt(
            base_system_prompt, retrieved_chunks, state.current_context
        )
    else:
        system_content = base_system_prompt

    # Build standard messages list
    messages = [{"role": "system", "content": system_content}]
    for m in state.messages:
        role = "user" if m["role"] == "user" else "assistant"
        messages.append({"role": role, "content": m["content"]})
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
    if retrieved_chunks and should_use_rag(user_msg, has_documents=has_documents):
        serialized_chunks = build_citation_map(retrieved_chunks)

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
                "cited_ids": extract_citation_ids(accumulated_text, max_id=max_citation_id)
            })
            
            # Cache answers if quiz context
            if state.current_context == "quiz":
                state.last_question = user_msg
                state.last_answer = extract_answer_from_response(accumulated_text)

            persist_session(session_id, state)

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
                "cited_ids": extract_citation_ids(final_content, max_id=max_citation_id)
            })
            persist_session(session_id, state)
            yield err_msg

    headers = {
        "Access-Control-Expose-Headers": "X-RAG-Sources",
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
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in (".txt", ".pdf"):
        raise HTTPException(status_code=400, detail="Hanya mendukung file .txt atau .pdf")

    # Read file content safely
    try:
        content_bytes = await file.read()
        
        from services.document_loader import extract_document
        try:
            raw_text = extract_document(content_bytes, file.filename, file_extension[1:])
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="File kosong atau tidak dapat diekstrak")

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
    if not query or not filename:
        return []
    
    # Filter chunks belonging to this document, doing defensive checking for BUG-06
    doc_chunks = []
    for c in state.doc_chunks:
        src = c.source_filename if hasattr(c, "source_filename") else c.get("source_filename", c.get("source", ""))
        if src == filename:
            doc_chunks.append(c)
            
    if not doc_chunks:
        return []
        
    from services.semantic_search import compute_cosine_similarity, get_embeddings_batch
    
    # Try fetching query embedding
    query_emb_list = get_embeddings_batch([query])
    
    # Precise substring fallback if embedding API fails
    if not query_emb_list or len(query_emb_list) == 0:
        results = []
        q_lower = query.lower()
        for c in doc_chunks:
            c_content = c.content if hasattr(c, "content") else c.get("content", "")
            c_index = c.chunk_index if hasattr(c, "chunk_index") else c.get("chunk_index", 0)
            if q_lower in c_content.lower():
                results.append({
                    "content": c_content,
                    "chunk_index": c_index,
                    "score": 0.85
                })
        return results

    query_emb = query_emb_list[0]
    
    # Batch-generate embeddings for any chunk missing it (BUG-04 Optimization)
    missing_indices = []
    missing_texts = []
    for idx, c in enumerate(doc_chunks):
        c_emb = getattr(c, "embedding", None) if hasattr(c, "embedding") else c.get("embedding", None)
        if not c_emb:
            c_content = c.content if hasattr(c, "content") else c.get("content", "")
            missing_indices.append(idx)
            missing_texts.append(c_content)
            
    if missing_texts:
        try:
            # Single batch HTTP request for all missing chunks
            new_embeddings = get_embeddings_batch(missing_texts)
            if new_embeddings:
                for idx, emb in zip(missing_indices, new_embeddings):
                    c = doc_chunks[idx]
                    if hasattr(c, "embedding"):
                        c.embedding = emb
                    elif isinstance(c, dict):
                        c["embedding"] = emb
        except Exception as e:
            print(f"[Embedding Batch Error] Failed to generate batch embeddings: {e}")

    results = []
    
    # Perform semantic scoring
    for c in doc_chunks:
        c_content = c.content if hasattr(c, "content") else c.get("content", "")
        c_index = c.chunk_index if hasattr(c, "chunk_index") else c.get("chunk_index", 0)
        c_emb = getattr(c, "embedding", None) if hasattr(c, "embedding") else c.get("embedding", None)
        
        if c_emb:
            score = compute_cosine_similarity(query_emb, c_emb)
            results.append({
                "content": c_content,
                "chunk_index": c_index,
                "score": score
            })
            
    # Sort results by match relevance
    results.sort(key=lambda x: x["score"], reverse=True)
    persist_session(session_id, state)
    return {"results": results, "session_id": session_id}


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
            model="llama-3.3-70b-versatile"
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
        print(f"[Quiz Generation Error] {e}")
        return {
            "topic": topic,
            "question": f"Manakah dari berikut ini yang merupakan konsep dasar dari {topic}?",
            "options": [
                {"key": "A", "text": "Mengumpulkan data secara acak tanpa tujuan analitis."},
                {"key": "B", "text": "Penerapan algoritma cerdas untuk mengekstrak pola kognitif yang berguna."},
                {"key": "C", "text": "Menghapus seluruh memori cache server secara berkala."},
                {"key": "D", "text": "Membeli perangkat keras termahal untuk mempercepat komputasi biasa."}
            ],
            "correct": "B"
        }


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
            model="llama-3.3-70b-versatile",
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
        print(f"[MindMap Generation Error] {e}")
        return {
            "nodes": [
                {"id": "1", "label": topic, "type": "root", "desc": f"Topik utama tentang {topic}."},
                {"id": "2", "label": "Konsep Dasar", "type": "branch", "desc": "Dasar-dasar dan fundamental penting."},
                {"id": "3", "label": "Penerapan Praktis", "type": "branch", "desc": "Bagaimana konsep ini diterapkan di dunia nyata."},
                {"id": "4", "label": "Tantangan Utama", "type": "branch", "desc": "Hambatan dan tantangan dalam mempelajari topik ini."}
            ],
            "edges": [
                {"source": "1", "target": "2"},
                {"source": "1", "target": "3"},
                {"source": "1", "target": "4"}
            ]
        }


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
            model="llama-3.3-70b-versatile",
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
        print(f"[MindMap Expansion Error] {e}")
        new_id_1 = f"sub-{req.node_id}-1"
        new_id_2 = f"sub-{req.node_id}-2"
        return {
            "nodes": [
                {"id": new_id_1, "label": f"Detail {req.node_label}", "type": "sub-branch", "desc": f"Penjelasan detail mengenai {req.node_label}."},
                {"id": new_id_2, "label": f"Contoh {req.node_label}", "type": "sub-branch", "desc": f"Contoh penerapan nyata dari {req.node_label}."}
            ],
            "edges": [
                {"source": req.node_id, "target": new_id_1},
                {"source": req.node_id, "target": new_id_2}
            ]
        }


if __name__ == "__main__":

    import uvicorn
    uvicorn.run(
        "api:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True, 
        reload_dirs=["core", "services", "ui", "prompts"]
    )
