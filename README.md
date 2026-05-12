# 🎓 ScholarBot AI — Intelligent Study Assistant

> **AI-powered study companion** berbasis Groq + Llama 3.3 70B dengan conversational memory, personality modes, dan specialized learning features.

<!-- Screenshot Placeholder — Add screenshots/main.png, screenshots/chat.png, screenshots/features.png -->

---

## 📌 Deskripsi Project

**ScholarBot AI** adalah chatbot edukasi cerdas yang dirancang untuk membantu siswa dan mahasiswa dalam proses belajar. Dibangun dengan arsitektur **LLM-based NLP System** menggunakan Groq API + Llama 3.3 70B Versatile, ScholarBot mampu memberikan penjelasan materi, membuat rangkuman, menghasilkan soal latihan, dan merekomendasikan jalur belajar — semua dalam satu antarmuka Streamlit yang intuitif.

---

## ✨ Fitur Utama

### 🤖 AI Core
| Fitur | Deskripsi |
|-------|-----------|
| **LLM Integration** | Groq API + Llama 3.3 70B Versatile (~8000 tok/s) |
| **Context-Aware Response** | Memahami konteks percakapan multi-turn secara akurat |
| **Prompt Engineering** | System prompt yang dioptimalkan untuk domain edukasi |

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
- Menyebut nama & riwayat topik dalam respons (context-aware)
- Menampilkan **Memory Panel** real-time di sidebar

### ⚡ Learning Modes (5 Mode Belajar)
| Mode | Fungsi |
|------|--------|
| 📚 **Tutor Mode** | Penjelasan konsep mendalam |
| ✍️ **Rangkum Materi** | Summarisasi ke poin penting |
| 🧪 **Quiz Generator** | Buat soal latihan otomatis |
| 🗺️ **Mind Map** | Outline & struktur materi |
| 💡 **Rekomendasi Belajar** | Roadmap belajar personal |

---

## 🏗️ Arsitektur Sistem

```
User Input (Streamlit UI)
        │
        ▼
 ┌─────────────────┐
 │  Session State  │  ← Conversational Memory
 │  (nama, topik)  │
 └────────┬────────┘
          │
          ▼
 ┌─────────────────┐
 │  System Prompt  │  ← Prompt Engineering
 │  Builder        │     (personality + memory)
 └────────┬────────┘
          │
          ▼
 ┌─────────────────┐
 │  Groq API +     │  ← LLM-based NLP System
 │  Llama 3.3 70B  │
 └────────┬────────┘
          │
          ▼
 ┌─────────────────┐
 │  Response       │  ← AI Agent Behavior
 │  Processing     │
 └────────┬────────┘
          │
          ▼
   Streamlit UI (Chat Render)
```

---

## 🚀 Cara Menjalankan

### 1. Clone Repository
```bash
git clone https://github.com/username/scholarbot-ai.git
cd scholarbot-ai
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup API Key (GRATIS!)
1. Buka **[console.groq.com/keys](https://console.groq.com/keys)**
2. Login (gratis — pakai Google/GitHub)
3. Klik **"Create API Key"**
4. Copy key dan paste ke file `.env`

```bash
# Copy file template
cp .env.example .env

# Edit dan masukkan Groq API key kamu
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
```

> 💡 **Alternatif:** Masukkan API key langsung di sidebar aplikasi tanpa file `.env`

### 4. Jalankan Aplikasi
```bash
streamlit run app.py
```

Buka browser di `http://localhost:8501` 🎉

---

## 📁 Struktur Folder

```
scholarbot-ai/
│
├── app.py              # Main application (Streamlit + Groq/Llama)
├── requirements.txt    # Python dependencies
├── .env.example        # Template environment variables
├── .env                # API key (jangan di-commit!)
├── README.md           # Dokumentasi ini
├── .gitignore          # Exclude .env dan cache
│
└── screenshots/
    ├── main.png        # Halaman utama
    ├── chat.png        # Contoh percakapan
    └── features.png    # Fitur unik
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend/UI** | Streamlit 1.35+ |
| **AI Model** | Llama 3.3 70B Versatile (via Groq API) |
| **AI SDK** | `groq` SDK |
| **Config** | `python-dotenv` |
| **Language** | Python 3.10+ |

---

## 💡 Konsep Teknis

### Prompt Engineering
System prompt dibangun secara dinamis berdasarkan:
- Pilihan personality mode user
- Nama user yang tersimpan di session
- Riwayat topik yang sudah dibahas
- Konteks mode belajar aktif

### Conversational Memory
Menggunakan **Streamlit Session State** sebagai in-memory store:
```python
st.session_state.user_name        # Nama user
st.session_state.topics_discussed  # List topik
st.session_state.messages          # History chat
```

### AI Agent Behavior
ScholarBot berperilaku sebagai agen edukasi dengan:
- **Goal-oriented responses**: Selalu mengarah pada pemahaman user
- **Domain specialization**: Fokus pada konteks belajar dan edukasi
- **Adaptive tone**: Menyesuaikan gaya bahasa dengan personality mode
- **Context retention**: Menyambungkan topik antar percakapan

### Streaming & Performance
Groq API menyediakan inference speed ~8000 tokens/detik, jauh lebih cepat dari provider lain di tier yang sama, menjadikan pengalaman chat terasa natural dan responsif.

---

## 📸 Screenshots

Ambil screenshot aplikasi dengan cara:
```bash
# Jalankan app
streamlit run app.py

# Screenshot browser di http://localhost:8501
# Simpan ke folder screenshots/ dengan nama:
#   - main.png       → Halaman utama
#   - chat.png       → Contoh percakapan
#   - features.png   → Mode Belajar / Quiz
```

| Halaman Utama | Percakapan | Mode Quiz |
|:---:|:---:|:---:|
| *(tambah main.png)* | *(tambah chat.png)* | *(tambah features.png)* |

---

## 👨‍💻 Developer

Dibuat sebagai **Final Project AI Chatbot Application**

- Framework: Streamlit
- Model: Llama 3.3 70B Versatile (via Groq API)
- Kategori: Education Tutor Bot
- API Provider: Groq (Free Tier)

---

## 📄 License

MIT License — Free to use and modify.
