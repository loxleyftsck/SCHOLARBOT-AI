# 🎓 ScholarBot AI v3 — Lightweight RAG Edition

> **AI-powered educational chatbot** dengan kemampuan **Document-Based RAG** yang ringan dan efisien.
> Berbasis **Groq API + Llama 3.3 70B** dengan modular architecture, personality modes, conversational memory, dan fitur RAG untuk menjawab pertanyaan berdasarkan materi yang di-upload.

<!-- Screenshot Placeholder — Add screenshots/main.png, screenshots/chat.png, screenshots/features.png -->

---

## 📌 Deskripsi Project

**ScholarBot AI v3** adalah chatbot edukasi yang ditingkatkan dengan fitur **RAG (Retrieval-Augmented Generation)**. Dengan upload materi belajar (.txt / .pdf), ScholarBot dapat mengambil konteks relevan dari dokumen untuk memberikan jawaban yang lebih akurat dan kontekstual.

Didesain dengan arsitektur **LLM-based NLP System** menggunakan Groq API + Llama 3.3 70B Versatile (~8000 tok/s). ScholarBot memberikan penjelasan materi, membuat rangkuman, menghasilkan soal latihan, dan merekomendasikan jalur belajar — semua dalam satu antarmuka Streamlit yang intuitif.

---

## ✨ Fitur Utama

### 🤖 AI Core
| Fitur | Deskripsi |
|--------|-----------|
| **LLM Integration** | Groq API + Llama 3.3 70B Versatile (~8000 tok/s) |
| **Context-Aware Response** | Memahami konteks percakapan multi-turn secara akurat |
| **Prompt Engineering** | System prompt yang dioptimalkan untuk domain edukasi |
| **RAG Pipeline** | Document retrieval tanpa vector database (keyword-based) |

### 🎭 Personality Modes (4 Mode)
| Mode | Karakter |
|------|---------|
| 🎓 **Formal Tutor** | Bahasa akademis, terstruktur, referensial |
| 😊 **Santai & Friendly** | Kasual, supportif, ramah pemula |
| ⚡ **Gen Z Mode** | Gaul, ekspresif, engaging |
| 💼 **Expert Consultant** | Analitis, mendalam, berbasis data |

### 🧠 Conversational Memory
- Mengingat **nama user** di seluruh sesi
- Melacak **topik yang sudah dibahas**
- Menyimpan **nama & riwayat topik** dalam respons (context-aware)
- Menampilkan **Memory Panel** real-time di sidebar
- Menyimpan **history percakapan** untuk kelanjutan sesi

### 🎓 RAG Features (v3 Baru)
| Fitur | Deskripsi |
|--------|-----------|
| **📄 Upload Dokumen** | Upload .txt atau .pdf dari sidebar |
| **📖 Ekstraksi Teks** | Ekstraksi otomatis dari PDF (pypdf) dan TXT |
| **✂️ Chunking** | Pecah teks menjadi bagian relevan (paragraph/sentence) |
| **🔍 Retrieval** | Keyword matching dengan scoring tanpa embedding |
| **📌 Context Injection** | Mengambil konteks dokumen ke prompt |
| **💡 Lightweight** | Tidak ada vector DB, tidak ada LangChain — cepat |

### ⚡ Learning Modes (5 Mode Belajar)
| Mode | Fungsi |
|------|--------|
| 📚 **Tutor Mode** | Penjelasan konsep mendalam |
| ✍️ **Rangkum Materi** | Summarisasi ke poin penting |
| 🧪 **Quiz Generator** | Buat soal latihan otomatis |
| 🗺️ **Mind Map** | Buat outline & struktur materi |
| 💡 **Rekomendasi Belajar** | Roadmap belajar personal |

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Streamlit UI                         │   │
│  │    ┌──────────┐                                      │   │
│  │    │  Sidebar  │      Chat Input                   │   │
│  │    │  │   ┌──────┴──────┐                    │   │
│  │    │  ├─ Upload  │   Messages │                       │   │
│  │    │  ├─ Person-│   ──────>                         │   │
│  │    │  │  ality   │   Groq API                          │   │
│  │    │  └────────┘    (Llama 3.3)                       │   │
│  │    └──────────┘                  │   Response  │   │
│  │        │                                   ──────>            │   │
│  └──────────────────────────────────────────────┐│
│                                             │   │
│  ┌────────────────────────────────────┐         │
│  │       Core Modules              │         │
│  │  ┌────────────────────────────┐  │         │
│  │  │ Prompt Building         │         │
│  │  ├─ System Prompt         │         │
│  │  ├─ RAG Context        │         │
│  │  ├─ Message Assembly     │         │
│  │  └─ Intent Detection     │         │
│  │  ┌────────────────────┐  │         │
│  │  │  Services Layer    │         │
│  │  │  ├─ Doc Loader       │         │
│  │  │  ├─ Chunker         │         │
│  │  │  └─ Retriever       │         │
│  │  └────────────────────┘  │         │
│  └────────────────────────────┘         │
│                                             │
│  ┌────────────────────────────────────┐         │
│  │       Storage Layer              │         │
│  │  ├─ JSON Persistence        │         │
│  │  └─ Session Management      │         │
│  └────────────────────────────────────┘         │
│                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Target Pengguna

ScholarBot AI dirancang untuk siapa saja yang ingin belajar secara lebih cerdas dan interaktif.

**Siswa SMA** yang ingin memahami materi pelajaran dengan cara yang lebih menarik dari textbook — bisa minta penjelasan ulang, buat soal latihan, atau upload catatan dari guru.

**Mahasiswa** yang menghadapi materi kompleks di semester awal dan butuh AI tutor yang bisa diajak diskusi, jelasin konsep berulang kali tanpa judgment, dan bantu rangkum bahan ajaran.

**Self-learner** yang belajar secara mandiri dari kursus online, buku, atau dokumen — upload materi dari internet, terus tanya langsung ke chatbot tanpa perlu buka banyak tab.

**Pengguna yang butuh AI tutor interaktif** — bukan sekadar search engine, tapi bisa diajak ngobrol dua arah, dikasih soal, minta pembahasan, dan terus lanjut dari mana mereka berhenti.

ScholarBot bukan pengganti guru atau buku. Tapi bisa jadi companion yang selalu tersedia kapan pun kamu butuh bantuan belajar.

---

## 💡 Bagaimana ScholarBot AI Membantu Pengguna

ScholarBot AI dirancang untuk membuat proses belajar terasa lebih natural dan efektif.

**Memahami dengan Cara Sendiri** — Kamu bisa tanya pakai bahasa sehari-hari, tanpa harus rumusin pertanyaan dalam format akademis. объясняет materi pakai kata-kata yang kamu pahami, bukan definisi dari kamus.

**Latihan Tanpa Batas** — Butuh tambahan soal untuk persiapan ujian? ScholarBot bisa generate soal pilihan ganda atau essay tentang topik yang kamu指定, lengkap dengan kunci jawaban dan pembahasan.

**Belajar dari Materimu Sendiri** — Upload rangkuman, catatan, slide, atau e-book dalam format TXT atau PDF. ScholarBot akan membaca dokumen tersebut dan menjawab pertanyaan berdasarkan isi materimu — bukan dari pengetahuan generik internet.

**Konteks Terjaga di Setiap Percakapan** — Tidak perlu ulang-ulang penjelasan. Kamu tanya "jelaskan X", terus lanjut "kasih contoh", ScholarBot ingat konteks dari pesan sebelumnya.

**Gaya Belajar yang Sesuai** — Pilih personality mode yang cocok: formal untuk belajar serius, santai untuk diskusi kasual, Gen Z untuk vibe yang lebih relatable, atau expert untuk analisis mendalam.

**Interaktif dan Responsif** — Tidak monoton. Kamu bisa minta hint, minta penjelasan ulang, minta buat rangkuman, atau minta roadmap belajar — semua dalam satu chatbot yang sama.

ScholarBot membuat belajar terasa seperti ngobrol dengan tutor pribadi yang tidak pernah kehabisan kesabaran.

---

## 🛠️ Tech Stack

| Komponen | Teknologi | Deskripsi |
|-----------|----------|---------|
| **Frontend** | Streamlit 1.35+ | UI framework untuk aplikasi Python |
| **AI Backend** | Groq API | LLM inference API (Llama 3.3 70B) |
| **LLM Model** | Llama 3.3 70B Versatile | Context window 128k tok |
| **Doc Processing** | pypdf | PDF text extraction |
| **Chunking** | Native Python | Paragraph & fixed-size splitting |
| **Retrieval** | Keyword matching + TF scoring | Tidak ada vector DB |
| **Persistence** | JSON file-based | Session storage di `storage/data/sessions/` |
| **Env Mgmt** | python-dotenv | Configuration via environment variables |

---

## 📦 Struktur Project

```
scholarbot/
│
├── app.py                       # Main Streamlit application
├── requirements.txt               # Python dependencies
├── README.md                     # Dokumentasi project
├── .env                         # API key (tidak ikut git)
├── .env.example                  # Template .env (untuk commit)
│
├── config/
│   ├── __init__.py
│   └── settings.py           # Konfigurasi aplikasi
│
├── core/
│   ├── __init__.py           # Ekspor modul core
│   ├── llm_client.py          # Abstraksi Groq API
│   ├── session_helpers.py      # Prompt builder, intent detection
│   ├── memory_manager.py       # Schema session state, mutations
│   └── rag_context.py          # RAG context injection (v3)
│
├── prompts/
│   ├── __init__.py
│   ├── personalities.py        # 4 mode personality system prompts
│   └── templates.py           # 5 learning mode templates
│
├── services/
│   ├── __init__.py           # Ekspor modul services
│   ├── document_loader.py      # TXT/PDF extraction (v3)
│   ├── chunker.py             # Text chunking (v3)
│   └── retriever.py           # Keyword-based retrieval (v3)
│
├── ui/
│   ├── __init__.py
│   ├── sidebar.py              # Konfigurasi sidebar
│   ├── uploader.py             # RAG uploader UI (v3)
│   └── styles.py              # Custom CSS untuk UI
│
├── utils/
│   ├── __init__.py
│   ├── token_counter.py       # Estimasi token & manajemen konteks
│   └── validators.py          # Validasi input & API key format
│
├── storage/
│   ├── __init__.py
│   └── json_store.py          # JSON file persistence
│
└── assets/
    └── Logo.png               # Logo aplikasi
```

---

## 🚀 Cara Menjalankan

### Prasyarat
- Python 3.11+
- Internet koneksi (untuk Groq API)
- Groq API Key (dapatkan gratis di [console.groq.com/keys](https://console.groq.com/keys))

### Langkah-Langkah

1. **Clone repository**
   ```bash
   git clone https://github.com/loxleyftsck/SCHOLARBOT-AI.git
   cd scholarbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment**
   ```bash
   cp .env.example .env
   # Edit .env dan tambahkan API key Groq:
   # GROQ_API_KEY=gsk_your_key_here
   ```

4. **Jalankan aplikasi**
   ```bash
   streamlit run app.py
   ```

5. **Buka browser**
   ```
   http://localhost:8501
   ```

---

## 🔧 Konfigurasi

| Environment Variable | Deskripsi |
|-------------------|-----------|
| `GROQ_API_KEY` | Groq API Key (wajib untuk fitur AI) |
| `MODEL_NAME` | Nama model (default: llama-3.3-70b-versatile) |
| `MODEL_TEMPERATURE` | Temperature sampling (default: 0.7) |
| `MODEL_MAX_TOKENS` | Max token per response (default: 2048) |
| `APP_TITLE` | Judul aplikasi |
| `APP_LAYOUT` | Tampilan layout (default: "wide") |
| `APP_SIDEBAR_STATE` | Sidebar state (default: "expanded") |

---

## 📊 RAG Pipeline (v3)

### Alur Dokumen → Jawaban

```
User Upload (.txt / .pdf)
        │
        ▼
services/document_loader.py
        │
        ├── extract_txt(file_bytes)  → plain text
        └── extract_pdf(file_bytes)  → plain text
        │
        ▼
services/chunker.py
        │
        └── chunk_text(text)  → List[Chunk]
            │   - paragraph-based untuk dokumen terstruktur
            │   - size-based untuk teks panjang
        │
        ▼
services/retriever.py
        │
        └── retrieve(query, chunks, top_k=3)  → List[RetrievedChunk]
            │   - Keyword overlap scoring
            │   - TF (term frequency) boost
            │   - Length density penalty
        │
        ▼
core/rag_context.py
        │
        └── build_rag_system_prompt(...)  → system prompt + RAG instruction
        │
        ▼
core/session_helpers.py
        │
        └── call_llama(...)  → send ke Groq API
            │   - Menginject konteks dokumen
            │   - Mempertahankan konteks percakapan
        │
        ▼
Llama 3.3 70B (Groq API)
        │
        ▼
Response → User
```

### Pengambilan Keputusan Retrieval

**Mengapa Keyword Bukan Vector Database?**

1. **Ringan** — Tidak ada embedding yang komputasi, retrieval cepat
2. **Edukasi** — Materi sekolah sering struktur, keyword matching efektif
3. **Demokratis** — Tidak ada infrastructure tambahan untuk deployment
4. **Efisiensi** — Keyword scoring O(n*m) vs vector search O(n log m)
5. **Transparan** — Mudah dimengerti algoritmanya untuk debugging

---

## 📖 Fitur Detail

### Context Tracking

ScholarBot memahami hubungan antar pesan dengan:

- **Konteks percakapan** — "Buat soal" → "Jawab" → menjawab soal yang benar
- **Referensi implicit** — "Bahaskan" → menjelaskan pembahasan soal terakhir
- **RAG awareness** — Saat dokumen di-upload, jawaban mengutamakan materi

### Document Handling

- **TXT upload** — Encoding otomatis (UTF-8, Latin-1, CP1252)
- **PDF upload** — Ekstraksi teks dari halaman menggunakan pypdf
- **Chunking strategy** — Auto-detect paragraph vs size-based chunking
- **Multi-document** — Upload hingga 5 dokumen sekaligus
- **Clear dokumen** — Hapus semua materi dari session

### Error Handling

- **Upload failure** — Pesan error jelas untuk user
- **Document parse error** — Handle PDF rusak atau tidak terbaca
- **Retrieval fallback** — Jika tidak ada konteks relevan, gunakan pengetahuan umum

---

## 🚀 Future Improvements

### v3.2 — Enhancement (Planned)
- [ ] Multi-document retrieval (cross-document scoring)
- [ ] Better chunking strategies (semantic boundary detection)
- [ ] Document summarization sebelum chunking
- [ ] Re-ranking dengan lebih banyak faktor
- [ ] UI: preview dokumen yang di-upload
- [ ] UI: search dalam dokumen
- [ ] Streaming responses untuk experience lebih cepat

### v4.0 — Advanced (Future)
- [ ] Vector database integration (ChromaDB / FAISS)
- [ ] Semantic retrieval dengan embedding model
- [ ] Multi-agent workflow (specialized tutors)
- [ ] Persistent memory across sessions
- [ ] Voice interaction (text-to-speech)
- [ ] Mobile optimization
- [ ] Inline citations dengan document reference
- [ ] Chat export as PDF/Word document

### Long-term Vision
ScholarBot dirancang untuk berevolusi menjadi intelligent learning companion yang bisa beradaptasi dengan gaya belajar setiap pengguna — dari siswa SMA sampai profesional yang sedang reskilling.

---

## 👨‍💻 Developer

**Developed by:** Herald Michain Samuel Theo

📧 **Contact:** [heraldmsamueltheo@gmail.com](mailto:heraldmsamueltheo@gmail.com)

**Fields of Interest:**
- AI Engineering
- Conversational AI
- Intelligent Tutoring Systems
- Lightweight RAG Systems

---

## 🐛 Troubleshooting

### Scenario 1: Belajar Materi Sekolah
```
User: Upload "rangkuman_ekonomi.pdf"
Bot: 📄 1 dokumen loaded (rangkuman_ekonomi.pdf)

User: "Apa itu elastisitas?"
Bot: [RAG] Menemukan 3 bagian dari rangkuman_ekonomi.pdf
    Elastisitas adalah kemampuan permintaan dan penawaran...
    Berdasarkan materi di atas, elastisitas adalah...

User: "Berikan contohnya"
Bot: [RAG] Menemukan 3 bagian dari rangkuman_ekonomi.pdf
    Contoh elastisitas dalam materi...
```

### Scenario 2: Membuat Soal dari Materi
```
User: Upload "notes_biology.txt"
Bot: 📄 1 dokumen loaded (notes_biology.txt)

User: "Buat 5 soal tentang sistem pernapasan"
Bot: [RAG] Berdasarkan notes_biology.txt dan soal di atas...
    Soal 1: Apa fungsi utama sistem pernapasan?
    [Dokumen notes_biology.txt]
    Berdasarkan materi di atas, sistem pernapasan adalah...
    Soal 2: [Dokumen notes_biology.txt]
    ...
```

### Scenario 3: Diskusi Interaktif
```
User: Upload "ringkasan_ppt.pdf"
Bot: 📄 1 dokumen loaded (ringkasan_ppt.pdf)

User: "Jelaskan tentang slide 3-5"
Bot: [RAG] Menemukan 3 bagian dari ringkasan_ppt.pdf
    [Dokumen ringkasan_ppt.pdf] Slide 3-5 membahas tentang...

User: "Bagaimana keterkaitannya dengan slide 6-8?"
Bot: [RAG] Menemukan 3 bagian dari ringkasan_ppt.pdf
    [Dokumen ringkasan_ppt.pdf] Tidak menemukan tentang slide 6-8
    dalam materi yang di-upload, hanya terdapat slide 1-5.
    Mungkin maksud Anda slide lanjutan atau bukan bagian presentasi ini?
```

---

## 🐛 Troubleshooting

### Upload Dokumen Gagal
```
Masalah: File tidak mau di-upload
Solusi: Cek tipe file (.txt atau .pdf), ukuran maksimal 10MB
```

### PDF Tidak Bisa Dibaca
```
Masalah: "Gagal ekstrak PDF" atau "PDF tidak memiliki teks"
Solusi: Pastikan bukan scanned PDF (hanya gambar). Gunakan PDF yang
         searchable text.
```

### Tidak Ada Jawaban dari Dokumen
```
Masalah: "Bot memberikan jawaban generik" / "Saya tidak tahu"
Solusi: Cek apakah dokumen benar-benar berisi materi yang relevan.
         Coba gunakan keyword yang lebih spesifik saat bertanya.
```

### Token Limit Exceeded
```
Masalah: Pesan error tentang token limit
Solusi: Hapus beberapa pesan lama (Reset Chat)
         atau hapus dokumen besar untuk menghemat konteks.
```

---

## 📄 API Key (Groq)

Dapatkan API key gratis di: [console.groq.com/keys](https://console.groq.com/keys)

**Catatan Keamanan:**
- Jangan pernah commit `.env` file yang berisi API key nyata
- Gunakan `.env.example` sebagai template untuk commit
- API key disimpan secara lokal saja, tidak dikirim ke server

---

## 📚 Referensi

- [Groq API Documentation](https://console.groq.com/docs/quickstart)
- [Llama 3.3 Model Card](https://llama.meta.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [PyPDF2 Documentation](https://pypdf.readthedocs.io/)

---

## 📜 License

Project ini untuk tujuan edukasi dan pembelajaran.

Dibuat dengan 💜 untuk komunitas belajar Indonesia.

---

**Versi:** v3.1 (Lightweight RAG Edition) — Stable Release
**Tanggal:** Mei 2026
**Status:** ✅ Production-Ready

---

## 🧪 Use Case — Belajar Dengan RAG
