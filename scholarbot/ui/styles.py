"""UI styles for ScholarBot AI.

Editorial warm minimalism v4 — clean, modern, and absolutely premium.
Design system: DM Serif Display + DM Sans, warm cream palette,
consistent SVG icons, no glow, 0.15s transitions only.
"""

from ui.tokens import build_css_variables

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

{build_css_variables()}

/* ═══════════════════════════════════════════════════════════════════
   GLOBAL RESET & THEMING
   ═══════════════════════════════════════════════════════════════════ */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body {{
    background: #FAF6F0 !important;
    font-family: 'DM Sans', sans-serif !important;
}}

[data-testid="stAppViewContainer"] {{
    background: #FAF6F0 !important;
}}

/* Clean up Streamlit chrome */
[data-testid="stDecoration"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
footer {{ display: none !important; }}

/* ═══════════════════════════════════════════════════════════════════
   SIDEBAR - PREMIUM MINIMAL DESIGN
   ═══════════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {{
    background-color: #F5EFEB !important;
    border-right: 1px solid #EAE2D8 !important;
    padding: 24px 16px !important;
}}

[data-testid="stSidebar"] > div:first-child {{
    background-color: #F5EFEB !important;
}}

/* ── Header ── */
.scholar-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 4px 20px 4px;
    border-bottom: 1px solid #EAE2D8;
    margin-bottom: 24px;
}}

.scholar-logo-wrapper {{
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: #FDFCFA;
    border: 1px solid #EADFCF;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #4A3728;
    box-shadow: 0 2px 6px rgba(74, 55, 40, 0.04);
    flex-shrink: 0;
}}

.scholar-logo-wrapper svg {{
    width: 24px;
    height: 24px;
    stroke: #4A3728;
}}

.scholar-logo-wrapper img {{
    width: 100%;
    height: 100%;
    object-fit: contain;
    border-radius: 11px;
}}

.scholar-title {{
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.35rem;
    font-weight: 500;
    color: #1C1814;
    line-height: 1.1;
    letter-spacing: -0.01em;
}}

.scholar-sub {{
    font-size: 0.65rem;
    color: #8A7F74;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    margin-top: 2px;
}}

/* ── Section Labels ── */
.sidebar-section-title {{
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #8A7F74;
    margin: 20px 8px 8px 8px;
    font-family: 'DM Sans', sans-serif;
}}

/* ── Profile Mini Card ── */
.profile-mini-card {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: #FDFCFA;
    border: 1px solid #EADFCF;
    border-radius: 14px;
    margin-bottom: 20px;
    box-shadow: 0 2px 6px rgba(74, 55, 40, 0.03);
}}

.profile-avatar {{
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #EAE2D8;
    color: #4A3728;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'DM Serif Display', serif;
    font-size: 18px;
    font-weight: 500;
    flex-shrink: 0;
    border: 1px solid #EADFCF;
}}

.profile-info {{
    display: flex;
    flex-direction: column;
    gap: 2px;
}}

.profile-greeting {{
    font-size: 0.85rem;
    color: #1C1814;
    font-weight: 600;
    line-height: 1.2;
}}

.profile-subtext {{
    font-size: 0.7rem;
    color: #8A7F74;
    line-height: 1.2;
}}

/* ── Personality AI Selectbox ── */
[data-testid="stSidebar"] .stSelectbox {{
    margin-bottom: 20px !important;
}}

[data-testid="stSidebar"] .stSelectbox > div > div {{
    background: #FDFCFA !important;
    border: 1px solid #EADFCF !important;
    border-radius: 12px !important;
    color: #3D3632 !important;
    font-size: 0.85rem !important;
    padding: 0px 12px !important;
    min-height: 38px !important;
    display: flex !important;
    align-items: center !important;
    transition: all var(--transition-base) !important;
    box-shadow: 0 2px 6px rgba(74, 55, 40, 0.02) !important;
}}

[data-testid="stSidebar"] .stSelectbox > div > div:hover {{
    border-color: #C5BAB0 !important;
    transform: translateY(-1px) !important;
}}

/* ── Menu Buttons — Clean, minimal style with SVG Icons injected ── */
.sidebar-menu-item {{
    margin-bottom: 4px !important;
}}

[data-testid="stSidebar"] .stButton > button {{
    background: transparent !important;
    border: none !important;
    border-radius: 10px !important;
    color: #5C5243 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    padding: 8px 12px !important;
    width: 100% !important;
    text-align: left !important;
    box-shadow: none !important;
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    cursor: pointer !important;
}}

[data-testid="stSidebar"] .stButton > button:hover {{
    background: #EAE2D8 !important;
    color: #1C1814 !important;
    transform: translateX(3px) !important;
}}

[data-testid="stSidebar"] .stButton > button:active {{
    background: #DFD7CD !important;
    transform: translateX(1px) !important;
}}

/* Injected SVG Icons for buttons via ::before pseudo-elements */
.st-key-menu_belajar button::before {{
    content: "";
    display: inline-block;
    width: 18px;
    height: 18px;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' fill='none' stroke='%234A3728' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' viewBox='0 0 24 24'><path d='M4 19.5A2.5 2.5 0 0 1 6.5 17H20'/><path d='M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z'/></svg>");
    background-size: contain;
    background-repeat: no-repeat;
    flex-shrink: 0;
}}

.st-key-menu_rangkuman button::before {{
    content: "";
    display: inline-block;
    width: 18px;
    height: 18px;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' fill='none' stroke='%234A3728' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' viewBox='0 0 24 24'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/><polyline points='14 2 14 8 20 8'/><line x1='16' y1='13' x2='8' y2='13'/><line x1='16' y1='17' x2='8' y2='17'/><polyline points='10 9 9 9 8 9'/></svg>");
    background-size: contain;
    background-repeat: no-repeat;
    flex-shrink: 0;
}}

.st-key-menu_latihan button::before {{
    content: "";
    display: inline-block;
    width: 18px;
    height: 18px;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' fill='none' stroke='%234A3728' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' viewBox='0 0 24 24'><path d='M22 11.08V12a10 10 0 1 1-5.93-9.14'/><polyline points='22 4 12 14.01 9 11.01'/></svg>");
    background-size: contain;
    background-repeat: no-repeat;
    flex-shrink: 0;
}}

.st-key-menu_mindmap button::before {{
    content: "";
    display: inline-block;
    width: 18px;
    height: 18px;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' fill='none' stroke='%234A3728' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' viewBox='0 0 24 24'><circle cx='18' cy='5' r='3'/><circle cx='6' cy='12' r='3'/><circle cx='18' cy='19' r='3'/><line x1='8.59' y1='13.51' x2='15.42' y2='17.49'/><line x1='15.41' y1='6.51' x2='8.59' y2='10.49'/></svg>");
    background-size: contain;
    background-repeat: no-repeat;
    flex-shrink: 0;
}}

.st-key-menu_riwayat button::before {{
    content: "";
    display: inline-block;
    width: 18px;
    height: 18px;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' fill='none' stroke='%234A3728' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' viewBox='0 0 24 24'><circle cx='12' cy='12' r='10'/><polyline points='12 6 12 12 16 14'/></svg>");
    background-size: contain;
    background-repeat: no-repeat;
    flex-shrink: 0;
}}

.st-key-menu_reset button {{
    color: #A84040 !important;
}}

.st-key-menu_reset button:hover {{
    background: rgba(168, 64, 64, 0.06) !important;
    color: #8A2020 !important;
}}

.st-key-menu_reset button::before {{
    content: "";
    display: inline-block;
    width: 18px;
    height: 18px;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' fill='none' stroke='%23A84040' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' viewBox='0 0 24 24'><path d='M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8'/><polyline points='3 3 3 8 8 8'/></svg>");
    background-size: contain;
    background-repeat: no-repeat;
    flex-shrink: 0;
}}

.menu-upload-btn button::before {{
    content: "";
    display: inline-block;
    width: 18px;
    height: 18px;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' fill='none' stroke='%234A3728' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' viewBox='0 0 24 24'><path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/><polyline points='17 8 12 3 7 8'/><line x1='12' y1='3' x2='12' y2='15'/></svg>");
    background-size: contain;
    background-repeat: no-repeat;
    flex-shrink: 0;
}}

/* ── Upload Area in Sidebar ── */
.upload-status-box {{
    background: #FDFCFA;
    border: 1px dashed #EADFCF;
    border-radius: 12px;
    padding: 12px;
    text-align: center;
    font-size: 0.75rem;
    color: #8A7F74;
    margin-top: 8px;
    box-shadow: inset 0 1px 3px rgba(74, 55, 40, 0.01);
}}

/* ── ScholarPro Card ── */
.pro-card {{
    background: #FDFCFA;
    border: 1px solid #EADFCF;
    border-radius: 14px;
    padding: 16px;
    margin-top: 24px;
    box-shadow: 0 4px 12px rgba(74, 55, 40, 0.03);
    position: relative;
    overflow: hidden;
}}

.pro-card::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: #8B6914;
}}

.pro-header {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}}

.pro-icon {{
    width: 24px;
    height: 24px;
    color: #8B6914;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.pro-icon svg {{
    width: 16px;
    height: 16px;
    stroke: #8B6914;
    fill: rgba(139, 105, 20, 0.1);
}}

.pro-title {{
    font-size: 0.85rem;
    font-weight: 600;
    color: #1C1814;
}}

.pro-desc {{
    font-size: 0.72rem;
    color: #8A7F74;
    line-height: 1.3;
    margin-bottom: 12px;
}}

.pro-btn {{
    display: block;
    width: 100%;
    padding: 8px 12px;
    background: #EAE2D8;
    border: 1px solid #EADFCF;
    border-radius: 8px;
    color: #4A3728;
    text-align: center;
    font-size: 0.75rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.15s ease;
    cursor: pointer;
}}

.pro-btn:hover {{
    background: #4A3728;
    color: #FDFCFA;
    border-color: #4A3728;
}}

/* ═══════════════════════════════════════════════════════════════════
   MAIN CONTAINER & TYPOGRAPHY
   ═══════════════════════════════════════════════════════════════════ */
[data-testid="stMainBlockContainer"] {{
    max-width: var(--layout-content_max_width) !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding-left: 16px !important;
    padding-right: 16px !important;
    padding-top: 32px !important;
}}

/* ── Welcome Page Styling ── */
.welcome-text-container {{
    padding: 32px 0 16px 0;
}}

.welcome-title {{
    font-family: 'DM Serif Display', Georgia, serif !important;
    font-size: 2.5rem !important;
    font-weight: 400 !important;
    color: #1C1814 !important;
    line-height: 1.15 !important;
    letter-spacing: -0.02em !important;
    margin-bottom: 12px !important;
}}

.welcome-desc {{
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
    color: #5C5243 !important;
    max-width: 480px;
    margin-bottom: 24px;
}}

.mascot-container {{
    display: flex;
    justify-content: flex-end;
    align-items: center;
    padding-top: 16px;
}}

.section-title {{
    font-family: 'DM Serif Display', Georgia, serif !important;
    font-size: 1.35rem !important;
    font-weight: 500 !important;
    color: #1C1814 !important;
    margin: 32px 0 16px 0 !important;
}}

.welcome-spacer {{
    height: 48px;
}}

/* ── Lanjutkan Belajar Cards ── */
.learning-card {{
    background: #FDFCFA;
    border: 1px solid #EADFCF;
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 4px 12px rgba(74, 55, 40, 0.02);
    transition: all 0.15s ease;
    cursor: pointer;
}}

.learning-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(74, 55, 40, 0.05);
    border-color: #C5BAB0;
}}

.card-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
}}

.card-icon-wrapper {{
    width: 38px;
    height: 38px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}}

.card-icon-wrapper svg {{
    width: 20px;
    height: 20px;
}}

.card-icon-wrapper.brain {{ background: #EFF4FC; color: #4A6B8A; }}
.card-icon-wrapper.brain svg {{ stroke: #4A6B8A; }}

.card-icon-wrapper.flask {{ background: #EEF8F4; color: #4A7C6F; }}
.card-icon-wrapper.flask svg {{ stroke: #4A7C6F; }}

.card-icon-wrapper.globe {{ background: #FCF4ED; color: #8B6B3D; }}
.card-icon-wrapper.globe svg {{ stroke: #8B6B3D; }}

.card-info {{
    flex: 1;
    min-width: 0;
}}

.card-subject {{
    font-size: 0.85rem;
    font-weight: 600;
    color: #1C1814;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}

.card-progress-text {{
    font-size: 0.75rem;
    color: #8A7F74;
    font-weight: 500;
    margin-top: 1px;
}}

.card-progress-bar {{
    height: 5px;
    background: #EAE2D8;
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 8px;
}}

.card-progress-fill {{
    height: 100%;
    background: #7A6250;
    border-radius: 3px;
}}

.learning-card:hover .card-progress-fill {{
    background: #4A3728;
}}

.card-footer {{
    font-size: 0.68rem;
    color: #8A7F74;
}}

/* ═══════════════════════════════════════════════════════════════════
   CHAT INPUT BAR & SUGGESTION CHIPS (MATCHING MOCKUP)
   ═══════════════════════════════════════════════════════════════════ */
[data-testid="stChatInputContainer"] {{
    background: #FAF6F0 !important;
    padding: 12px 0 24px 0 !important;
    border-top: 1px solid #EAE2D8 !important;
}}

[data-testid="stChatInputContainer"] > div:first-child {{
    max-width: var(--layout-content_max_width) !important;
    margin-left: auto !important;
    margin-right: auto !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}}

/* Main input container */
[data-testid="stChatInputContainer"] .stChatInput {{
    background: #FDFCFA !important;
    border: 1px solid #EADFCF !important;
    border-radius: 18px !important;
    box-shadow: 0 4px 16px rgba(74, 55, 40, 0.03) !important;
    transition: all 0.2s ease !important;
    padding: 4px 6px !important;
}}

[data-testid="stChatInputContainer"] .stChatInput:focus-within {{
    border-color: #8B6914 !important;
    box-shadow: 0 4px 20px rgba(139, 105, 20, 0.06) !important;
}}

/* Textarea inside input */
[data-testid="stChatInputContainer"] .stChatInput textarea {{
    background: transparent !important;
    color: #1C1814 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
    padding: 10px 12px !important;
    line-height: 1.5 !important;
    border: none !important;
}}

[data-testid="stChatInputContainer"] .stChatInput textarea::placeholder {{
    color: #A39684 !important;
}}

/* Circular Walnut send button */
[data-testid="stChatInputContainer"] .stChatInput > div > div > button {{
    background: #4A3728 !important;
    color: #FDFCFA !important;
    border-radius: 50% !important;
    width: 38px !important;
    height: 38px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.15s ease !important;
    padding: 0 !important;
    border: none !important;
    box-shadow: 0 2px 6px rgba(74, 55, 40, 0.1) !important;
}}

[data-testid="stChatInputContainer"] .stChatInput > div > div > button:hover {{
    background: #5C4535 !important;
    transform: scale(1.04) !important;
}}

[data-testid="stChatInputContainer"] .stChatInput > div > div > button:active {{
    transform: scale(0.96) !important;
}}

/* Streamlit chat input icon change to clean arrow-up */
[data-testid="stChatInputContainer"] .stChatInput svg {{
    display: none !important;
}}

[data-testid="stChatInputContainer"] .stChatInput > div > div > button::after {{
    content: "↑";
    font-size: 1.2rem;
    font-weight: 500;
    line-height: 1;
}}

/* ── Disclaimer text below input ── */
.input-disclaimer {{
    font-size: 0.72rem;
    color: #A39684;
    text-align: center;
    margin-top: 8px;
    font-family: 'DM Sans', sans-serif;
}}

/* ── Suggestion Chips block ── */
.chips-container {{
    display: flex;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 16px;
    margin-bottom: 4px;
}}

[data-testid="stMainBlockContainer"] .chips-container .stButton > button {{
    background: #F5EFEB !important;
    border: 1px solid #EADFCF !important;
    border-radius: 20px !important;
    color: #5C5243 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 6px 14px !important;
    transition: all 0.15s ease !important;
    width: auto !important;
    box-shadow: none !important;
    cursor: pointer !important;
}}

[data-testid="stMainBlockContainer"] .chips-container .stButton > button:hover {{
    background: #FDFCFA !important;
    border-color: #C5BAB0 !important;
    color: #1C1814 !important;
    transform: translateY(-1px) !important;
}}

[data-testid="stMainBlockContainer"] .chips-container .stButton > button:active {{
    background: #EAE2D8 !important;
    transform: translateY(0) !important;
}}

/* Responsive refinements */
@media (max-width: 768px) {{
    .welcome-title {{
        font-size: 2rem !important;
    }}
    
    .learning-card {{
        margin-bottom: 12px;
    }}
}}
</style>
"""