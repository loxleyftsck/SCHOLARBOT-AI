import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ScholarBot AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global Reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0e1a !important;
    font-family: 'Sora', sans-serif !important;
    color: #e2e8f0 !important;
}

[data-testid="stAppViewContainer"] > .main {
    background: #0a0e1a !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1225 0%, #0a0e1a 100%) !important;
    border-right: 1px solid rgba(99, 179, 237, 0.15) !important;
}

[data-testid="stSidebar"] * { color: #cbd5e0 !important; }

/* ── Header ── */
.scholar-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 28px 28px 20px;
    border-bottom: 1px solid rgba(99,179,237,0.12);
    margin-bottom: 24px;
}
.scholar-logo {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, #63b3ed, #4299e1);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    box-shadow: 0 0 20px rgba(99,179,237,0.35);
    flex-shrink: 0;
}
.scholar-title { font-size: 1.25rem; font-weight: 700; color: #e2e8f0; line-height: 1.2; }
.scholar-sub   { font-size: 0.72rem; color: #63b3ed; letter-spacing: 0.08em; text-transform: uppercase; }

/* ── Sidebar Section Labels ── */
.sidebar-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4a5568 !important;
    padding: 0 20px;
    margin-bottom: 8px;
    margin-top: 20px;
}

/* ── Quick Action Buttons ── */
.quick-btns { display: flex; flex-direction: column; gap: 6px; padding: 0 12px; }
.quick-btn {
    background: rgba(99,179,237,0.07);
    border: 1px solid rgba(99,179,237,0.15);
    border-radius: 10px;
    padding: 10px 14px;
    color: #a0aec0 !important;
    font-family: 'Sora', sans-serif;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
    width: 100%;
}
.quick-btn:hover {
    background: rgba(99,179,237,0.15);
    border-color: rgba(99,179,237,0.4);
    color: #e2e8f0 !important;
}

/* ── Memory Card ── */
.memory-card {
    margin: 12px;
    background: rgba(99,179,237,0.06);
    border: 1px solid rgba(99,179,237,0.15);
    border-radius: 12px;
    padding: 14px;
}
.memory-item {
    display: flex; align-items: flex-start; gap: 8px;
    font-size: 0.78rem; color: #a0aec0; margin-bottom: 6px;
}
.memory-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #63b3ed; flex-shrink: 0; margin-top: 5px;
}

/* ── Main Chat Area ── */
.main-wrapper {
    max-width: 820px;
    margin: 0 auto;
    padding: 24px 32px 120px;
}

/* ── Chat Welcome ── */
.welcome-block {
    text-align: center;
    padding: 60px 20px 40px;
}
.welcome-icon {
    font-size: 3.5rem;
    margin-bottom: 16px;
    filter: drop-shadow(0 0 20px rgba(99,179,237,0.5));
}
.welcome-title {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #63b3ed, #90cdf4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}
.welcome-sub { color: #718096; font-size: 0.95rem; line-height: 1.6; }

/* ── Suggestion Chips ── */
.chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 28px; }
.chip {
    background: rgba(99,179,237,0.08);
    border: 1px solid rgba(99,179,237,0.2);
    border-radius: 20px;
    padding: 8px 16px;
    font-size: 0.8rem;
    color: #90cdf4;
    cursor: pointer;
}

/* ── Messages ── */
.msg-row { display: flex; gap: 12px; margin-bottom: 20px; align-items: flex-start; }
.msg-row.user { flex-direction: row-reverse; }

.avatar {
    width: 36px; height: 36px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
}
.avatar.bot  { background: linear-gradient(135deg, #63b3ed, #4299e1); box-shadow: 0 0 12px rgba(99,179,237,0.3); }
.avatar.user { background: linear-gradient(135deg, #667eea, #764ba2); }

.bubble {
    max-width: 78%;
    padding: 14px 18px;
    border-radius: 16px;
    font-size: 0.88rem;
    line-height: 1.65;
}
.bubble.bot {
    background: #141929;
    border: 1px solid rgba(99,179,237,0.15);
    color: #e2e8f0;
    border-radius: 4px 16px 16px 16px;
}
.bubble.user {
    background: linear-gradient(135deg, rgba(102,126,234,0.25), rgba(118,75,162,0.25));
    border: 1px solid rgba(102,126,234,0.3);
    color: #e2e8f0;
    border-radius: 16px 4px 16px 16px;
}
.msg-time { font-size: 0.68rem; color: #4a5568; margin-top: 4px; text-align: right; }

/* ── Typing Indicator ── */
.typing {
    display: flex; gap: 5px; align-items: center;
    padding: 14px 18px;
    background: #141929;
    border: 1px solid rgba(99,179,237,0.15);
    border-radius: 4px 16px 16px 16px;
    width: fit-content;
}
.dot { width:7px; height:7px; background:#63b3ed; border-radius:50%; animation: bounce 1.2s infinite; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-6px)} }

/* ── Input Bar ── */
.stChatInput > div {
    background: #141929 !important;
    border: 1px solid rgba(99,179,237,0.25) !important;
    border-radius: 16px !important;
}
.stChatInput textarea {
    background: transparent !important;
    color: #e2e8f0 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.88rem !important;
}
.stChatInput textarea::placeholder { color: #4a5568 !important; }

/* ── Streamlit Widget Overrides ── */
.stSelectbox > div > div {
    background: #141929 !important;
    border: 1px solid rgba(99,179,237,0.2) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}
.stTextInput > div > div > input {
    background: #141929 !important;
    border: 1px solid rgba(99,179,237,0.2) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Sora', sans-serif !important;
}
.stButton > button {
    background: linear-gradient(135deg, #4299e1, #3182ce) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(66,153,225,0.4) !important;
}

/* ── Dividers ── */
hr { border-color: rgba(99,179,237,0.1) !important; }

/* ── Streamlit default element cleanup ── */
.block-container { padding-top: 1rem !important; padding-bottom: 0 !important; }
[data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }
footer { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ─── Groq Setup ────────────────────────────────────────────────────────────────
API_KEY = os.getenv("GROQ_API_KEY", "")
groq_client = None
if API_KEY:
    groq_client = Groq(api_key=API_KEY)

PERSONALITIES = {
    "🎓 Formal Tutor": {
        "label": "Formal",
        "desc": "Terstruktur, akademis, dan detail",
        "system": (
            "Kamu adalah ScholarBot, asisten belajar AI yang profesional dan akademis. "
            "Gunakan bahasa Indonesia yang formal dan baku. "
            "Selalu susun jawaban secara terstruktur dengan poin-poin jelas. "
            "Gunakan istilah ilmiah yang tepat. "
            "Saat menjelaskan konsep, berikan definisi, penjelasan, dan contoh secara berurutan. "
            "Gunakan format yang rapi dengan heading dan bullet point bila perlu."
        ),
    },
    "😊 Santai & Friendly": {
        "label": "Santai",
        "desc": "Kasual, supportif, mudah dipahami",
        "system": (
            "Kamu adalah ScholarBot, teman belajar AI yang asik dan supportif! "
            "Pakai bahasa Indonesia yang santai dan friendly. "
            "Gunakan emoji sesekali biar lebih hidup. "
            "Kalau ada yang susah, pecah jadi bagian kecil yang gampang dimengerti. "
            "Semangatin user kalau mereka belajar sesuatu yang baru! "
            "Jangan terlalu kaku, ngobrol aja seperti teman."
        ),
    },
    "⚡ Gen Z Mode": {
        "label": "Gen Z",
        "desc": "Gaul, no cap, literally learning",
        "system": (
            "Lo adalah ScholarBot, asisten belajar yang literally the GOAT! "
            "Pakai bahasa campur Indo-Inggris gaya Gen Z. "
            "Gunakan kata-kata kekinian: no cap, literally, slay, vibe, bestie, lowkey, fr fr, etc. "
            "Tetap akurat dan informatif, tapi delivery-nya harus hits banget. "
            "Pakai emoji yang relevan. "
            "Kalau ada materi yang susah, bilang 'ngl ini emang challenging tapi kita bisa!' "
            "Bikin belajar jadi chill dan engaging."
        ),
    },
    "💼 Expert Consultant": {
        "label": "Expert",
        "desc": "Mendalam, analitis, berbasis data",
        "system": (
            "Kamu adalah ScholarBot, konsultan pendidikan AI tingkat lanjut. "
            "Berikan analisis mendalam dengan perspektif multi-dimensi. "
            "Hubungkan konsep dengan aplikasi nyata di dunia profesional. "
            "Tawarkan framework berpikir dan mental model yang kuat. "
            "Referensikan sumber atau tokoh relevan bila memungkinkan. "
            "Gunakan bahasa Indonesia profesional namun accessible. "
            "Selalu akhiri dengan insight atau perspektif yang actionable."
        ),
    },
}

MODES = {
    "📚 Tutor Mode": "Bantu saya memahami konsep ini secara mendalam dan berikan penjelasan yang mudah dimengerti.",
    "✍️ Rangkum Materi": "Tolong rangkum materi atau teks berikut menjadi poin-poin penting yang mudah diingat:",
    "🧪 Quiz Generator": "Buat 5 soal latihan (pilihan ganda atau essay) beserta kunci jawaban tentang topik:",
    "🗺️ Mind Map": "Buat outline/mind map terstruktur dari topik berikut, lengkap dengan sub-topik utama:",
    "💡 Rekomendasi Belajar": "Berikan roadmap dan rekomendasi sumber belajar terbaik untuk mempelajari:",
}

# ─── Session State Init ─────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "messages": [],
        "user_name": "",
        "personality": "😊 Santai & Friendly",
        "topics_discussed": [],
        "session_start": datetime.now().strftime("%H:%M"),
        "msg_count": 0,
        "active_mode": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ─── Helper: Build System Prompt ───────────────────────────────────────────────
def build_system_prompt():
    base = PERSONALITIES[st.session_state.personality]["system"]
    memory_parts = []
    if st.session_state.user_name:
        memory_parts.append(f"Nama user adalah {st.session_state.user_name}, sapa dengan namanya bila relevan.")
    if st.session_state.topics_discussed:
        recent = ", ".join(st.session_state.topics_discussed[-3:])
        memory_parts.append(f"Topik yang sudah dibahas sebelumnya: {recent}.")
    if memory_parts:
        base += " " + " ".join(memory_parts)
    base += (
        " Kamu fokus pada bidang edukasi dan pembelajaran. "
        "Saat user menanyakan hal di luar topik belajar, arahkan kembali dengan sopan. "
        "Selalu berikan jawaban yang akurat, bermanfaat, dan mendidik."
    )
    return base

# ─── Helper: Extract Topic ──────────────────────────────────────────────────────
def extract_topic(text: str) -> str | None:
    keywords = ["tentang", "mengenai", "soal", "materi", "belajar", "pelajaran", "konsep", "jelaskan"]
    lower = text.lower()
    for kw in keywords:
        if kw in lower:
            idx = lower.find(kw) + len(kw)
            snippet = text[idx:idx+40].strip().split()[0:4]
            if snippet:
                return " ".join(snippet)
    if len(text) < 50:
        return text.strip()
    return None

# ─── Helper: Call Groq Llama ───────────────────────────────────────────────────
# Groq API (FREE): https://console.groq.com/keys
# Model Llama-3.3-70B-Versatile: context 128k tokens, sangat cepat (8000 tok/s)

MODEL_NAME = "llama-3.3-70b-versatile"

def call_llama(user_msg: str) -> str:
    if not groq_client:
        return (
            "⚠️ **API Key belum dikonfigurasi.**\n\n"
            "Pastikan `GROQ_API_KEY` sudah ada di file `.env`, "
            "lalu restart aplikasi."
        )
    try:
        # Bangun messages list: system + history + user baru
        messages = [{"role": "system", "content": build_system_prompt()}]
        for m in st.session_state.messages:
            role = "user" if m["role"] == "user" else "assistant"
            messages.append({"role": role, "content": m["content"]})

        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Terjadi error: `{e}`\n\nPastikan API key valid dan koneksi internet aktif."

# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo & Title
    st.markdown("""
    <div class="scholar-header">
        <div class="scholar-logo">🎓</div>
        <div>
            <div class="scholar-title">ScholarBot</div>
            <div class="scholar-sub">AI Study Assistant</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Groq API Key input (if not in .env)
    if not API_KEY:
        st.markdown('<div class="sidebar-label">🔑 API Key</div>', unsafe_allow_html=True)
        st.caption("💡 Gratis di [console.groq.com](https://console.groq.com/keys)")
        key_input = st.text_input("Groq API Key", type="password", placeholder="gsk_...", label_visibility="collapsed")
        if key_input:
            groq_client = Groq(api_key=key_input)
            os.environ["GROQ_API_KEY"] = key_input
            globals()["API_KEY"] = key_input
            globals()["groq_client"] = groq_client
            st.success("✓ API Key Groq tersimpan!")
        st.markdown("---")

    # User Name Memory
    st.markdown('<div class="sidebar-label">👤 Profil Kamu</div>', unsafe_allow_html=True)
    name = st.text_input(
        "Nama kamu",
        value=st.session_state.user_name,
        placeholder="Masukkan namamu…",
        label_visibility="collapsed",
    )
    if name != st.session_state.user_name:
        st.session_state.user_name = name

    # Personality Selector
    st.markdown('<div class="sidebar-label">🎭 Mode Personality</div>', unsafe_allow_html=True)
    persona = st.selectbox(
        "Personality",
        list(PERSONALITIES.keys()),
        index=list(PERSONALITIES.keys()).index(st.session_state.personality),
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

    # Quick Action Modes
    st.markdown('<div class="sidebar-label">⚡ Mode Belajar</div>', unsafe_allow_html=True)
    for mode_label in MODES:
        if st.button(mode_label, key=f"mode_{mode_label}", use_container_width=True):
            st.session_state.active_mode = mode_label

    st.markdown("---")

    # Memory Display
    st.markdown('<div class="sidebar-label">🧠 Memory Session</div>', unsafe_allow_html=True)
    mem_html = '<div class="memory-card">'
    if st.session_state.user_name:
        mem_html += f'<div class="memory-item"><div class="memory-dot"></div><span>Nama: <b>{st.session_state.user_name}</b></span></div>'
    mem_html += f'<div class="memory-item"><div class="memory-dot"></div><span>Mulai: {st.session_state.session_start}</span></div>'
    mem_html += f'<div class="memory-item"><div class="memory-dot"></div><span>Pesan: {st.session_state.msg_count}</span></div>'
    if st.session_state.topics_discussed:
        topics_str = ", ".join(st.session_state.topics_discussed[-3:])
        mem_html += f'<div class="memory-item"><div class="memory-dot"></div><span>Topik: {topics_str}</span></div>'
    else:
        mem_html += '<div class="memory-item"><div class="memory-dot"></div><span style="color:#4a5568">Belum ada topik</span></div>'
    mem_html += "</div>"
    st.markdown(mem_html, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑️ Reset Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.topics_discussed = []
        st.session_state.msg_count = 0
        st.session_state.active_mode = None
        st.rerun()

# ─── MAIN AREA ──────────────────────────────────────────────────────────────────
st.markdown('<div class="main-wrapper">', unsafe_allow_html=True)

# Welcome screen
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
        <div class="chips">
            <span class="chip">📐 Jelaskan teorema Pythagoras</span>
            <span class="chip">🌏 Rangkum Perang Dunia II</span>
            <span class="chip">💻 Apa itu machine learning?</span>
            <span class="chip">🧪 Buat soal Kimia Kelas 12</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Render chat history
for msg in st.session_state.messages:
    is_user = msg["role"] == "user"
    row_cls = "user" if is_user else "bot"
    avatar  = "👤" if is_user else "🎓"
    bubble_cls = "user" if is_user else "bot"
    time_str = msg.get("time", "")
    st.markdown(f"""
    <div class="msg-row {row_cls}">
        <div class="avatar {row_cls}">{avatar}</div>
        <div>
            <div class="bubble {bubble_cls}">{msg["content"]}</div>
            <div class="msg-time">{time_str}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ─── Active Mode Pre-fill ───────────────────────────────────────────────────────
mode_placeholder = ""
if st.session_state.active_mode:
    mode_placeholder = MODES[st.session_state.active_mode]

# ─── Chat Input ─────────────────────────────────────────────────────────────────
user_input = st.chat_input(
    placeholder=mode_placeholder or "Tanya apa saja tentang pelajaran… ✏️",
)

if user_input:
    final_input = user_input
    if st.session_state.active_mode and not user_input.startswith(MODES[st.session_state.active_mode]):
        final_input = MODES[st.session_state.active_mode] + " " + user_input
        st.session_state.active_mode = None

    now = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({"role": "user", "content": final_input, "time": now})
    st.session_state.msg_count += 1

    # Extract & store topic
    topic = extract_topic(final_input)
    if topic and topic not in st.session_state.topics_discussed:
        st.session_state.topics_discussed.append(topic)

    # Get AI response
    with st.spinner(""):
        reply = call_llama(final_input)

    st.session_state.messages.append({"role": "assistant", "content": reply, "time": datetime.now().strftime("%H:%M")})
    st.rerun()
