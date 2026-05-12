"""UI styles for ScholarBot AI.

Extracted from app.py Phase 2 refactor.
Contains all custom CSS — no business logic.
"""

CSS = """
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
"""