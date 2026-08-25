# ScholarBot AI Learning Workspace - Project Roadmap

## Overview
ScholarBot is an AI-native educational assistant designed to provide an interactive, premium, and seamless learning experience. Phase 1 focused on creating a beautiful prototype using Streamlit with dynamic UI features. Phase 2 aims to migrate to a production-grade stack (React/Next.js + FastAPI) to unlock advanced interactions, persistent memory, and gamification.

## ✅ Phase 1: Prototype & UI Optimization (Completed)
- **Aesthetic Overhaul**: Implemented a warm beige/cream minimalist theme. Removed all default Streamlit visual clutter.
- **Dynamic Assets**: Embedded `mascot.png` securely in the sidebar using base64 encoding.
- **Interactive UI Components**:
  - Replaced native Streamlit chat with a custom React-based chat interface (`ui/chat_component.html`).
  - Added dynamic "Lanjutkan Belajar" (Continue Learning) cards that populate based on the current session's discussion history.
  - Resolved UI scroll bugs and added AI typing indicators.
- **Visual Mind Maps**:
  - Integrated `mermaid.js` client-side rendering directly into the React chat component.
  - Engineered LLM prompts (using Groq/LLaMA 3) to strictly output valid Mermaid syntax.
- **Performance Fixes**:
  - Stripped out artificial loop bottlenecks (e.g., `importlib.reload` on every interaction).
  - Implemented rendering throttles to handle Groq's high-speed token streaming without lagging the browser.

## 🚀 Phase 2: Production Web Application (Current/Next Focus)

### 1. Frontend Migration (React / Next.js) — [✅ COMPLETED]
**Goal**: Move away from Streamlit's limitations into a pure Single Page Application (SPA).
- **Setup**: React/Vite initialized in `scholarbot-web/` with full Tailwind CSS support.
- **Styling**: Ported beautiful editorial theme into pure responsive components with Framer Motion and Lucide icons.
- **Dynamic Connection**: Swapped static offline mocked generators with active `fetch` ReadableStream listeners connecting the browser to the FastAPI LLM stream in real-time.

### 2. Backend API Architecture (FastAPI) — [✅ COMPLETED]
**Goal**: Separate the AI logic from the UI to create a scalable backend service.
- **API Endpoints**: Designed high-performance FastAPI routes at `api.py` including `/api/chat` (Server-Sent Events streaming) and `/api/upload` (Form multipart PDF/TXT uploading).
- **Session Isolation**: Structured thread-safe, session-isolated data states (`SESSIONS`) to hold memory context, uploaded docs, and discussed topics per browser tab.

### 3. Persistent Memory & RAG (Retrieval-Augmented Generation) — [✅ COMPLETED]
**Goal**: Allow ScholarBot to "remember" user documents across sessions with semantic accuracy.
- **Lightweight Semantic Search**: Built zero-dependency dense vector Cosine Similarity search using NumPy and a free public Hugging Face Inference API (`all-MiniLM-L6-v2`) with a robust offline keyword fallback.
- **Adaptive Semantic Chunking**: Split text dynamically at sentence topic transitions based on consecutive embedding similarities using a dynamic 25th-percentile threshold.
- **RAG Upload Pipeline**: Connected React drag-and-drop to FastAPI RAG endpoint `/api/upload` with instant extraction and chunking of PDF and TXT.
- **Session Caching**: Embedded vector caches directly into the JSON session database for instant query retrieval.

### 4. Gamification & True Progress Tracking — [✅ COMPLETED]
**Goal**: Motivate users through real progress metrics.
- **Dynamic Quiz Generator**: Created `/api/quiz` endpoint using Groq LLaMA 3.3 70B to automatically generate 1-question multiple choice quizzes based on the current session's conversation history.
- **Quiz Scorer & Statistics**: Wired `InteractiveQuiz` in React to fetch dynamic AI quizzes and submit results to POST `/api/quiz/submit` to record progress in `SessionState`.
- **Mastery Progress Sidebar**: Directly integrated quiz scores to update user topic mastery scores and progress bars in real-time.

### 5. Citation System (Verifiable Answers) — [✅ COMPLETED]
**Goal**: Make every document-based claim traceable back to the exact chunk it came from.
- **Numbered Retrieval Context**: `format_retrieved_context` now labels each chunk `[1] Sumber: file (bagian n)` — the same marker the model is instructed to reuse inline.
- **Citation Rules in Prompt**: `RAG_INSTRUCTION` requires an inline `[n]` after every sentence drawn from the material, restricted to the ids actually supplied.
- **Citation Map & Guards**: `build_citation_map` serializes numbered sources for the SPA; `extract_citation_ids` records what the answer really used and `strip_invalid_citations` drops hallucinated ids.
- **Interactive UI**: `[n]` renders as a clickable badge that expands the source panel, scrolls to the matching card, and highlights it; uncited sources are dimmed.

## 🛠 Tech Stack Summary
- **AI Inference**: Groq API (LLaMA 3)
- **Current Architecture**: Python + Streamlit + React Components (HTML injects)
- **Target Architecture**: React/Next.js (Frontend) + FastAPI (Backend) + Vector DB
