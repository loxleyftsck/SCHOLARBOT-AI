"""Streamlit-React bridge utilities.

Provides functions to render custom React components within Streamlit,
passing data from Python to JavaScript seamlessly.
"""

import json
import streamlit.components.v1 as components
from pathlib import Path
from typing import List, Dict, Optional


def render_custom_chat(
    messages: List[Dict],
    is_typing: bool = False,
    streaming_message_id: Optional[str] = None,
    height: int = 600,
    key: Optional[str] = None
) -> None:
    """Render custom React chat component with Streamlit data.

    Args:
        messages: List of message dicts with keys: role, content, time, id
        is_typing: Whether to show typing indicator
        streaming_message_id: ID of message currently being streamed
        height: Component height in pixels
        key: Streamlit component key for state management
    """

    # Load HTML template
    template_path = Path(__file__).parent / "chat_component.html"
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    # Prepare messages data
    messages_data = []
    for msg in messages:
        messages_data.append({
            "id": msg.get("id", None),
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
            "time": msg.get("time", "")
        })

    # Inject data into HTML
    messages_json = json.dumps(messages_data, ensure_ascii=False)
    is_typing_json = json.dumps(is_typing)
    streaming_id_json = json.dumps(streaming_message_id)

    # Replace placeholders
    html_with_data = html_template.replace(
        "window.STREAMLIT_MESSAGES || []",
        f"window.STREAMLIT_MESSAGES = {messages_json}; window.STREAMLIT_MESSAGES"
    )
    html_with_data = html_with_data.replace(
        "window.STREAMLIT_IS_TYPING || false",
        f"window.STREAMLIT_IS_TYPING = {is_typing_json}; window.STREAMLIT_IS_TYPING"
    )
    html_with_data = html_with_data.replace(
        "window.STREAMLIT_STREAMING_ID || null",
        f"window.STREAMLIT_STREAMING_ID = {streaming_id_json}; window.STREAMLIT_STREAMING_ID"
    )

    # Render component
    components.html(html_with_data, height=height, scrolling=True)


def render_welcome_screen(
    user_name: str = "",
    suggestion_chips: List[tuple] = None
) -> None:
    """Render custom welcome screen with React.

    Args:
        user_name: User's name for personalized greeting
        suggestion_chips: List of (label, text) tuples for suggestion chips
    """

    if suggestion_chips is None:
        suggestion_chips = [
            ("Jelaskan Teorema Pythagoras", "Jelaskan teorema Pythagoras dengan contoh"),
            ("Buat rangkuman Perang Dunia II", "Rangkum Perang Dunia II"),
            ("Buat quiz tentang kimia", "Buat 5 soal kimia kelas 12"),
        ]

    card_data = {
        "Jelaskan Teorema Pythagoras": {
            "color": "#EFF4FC",
            "icon": "📐",
            "desc": "Belajar Teorema Pythagoras dengan contoh visual yang interaktif"
        },
        "Buat rangkuman Perang Dunia II": {
            "color": "#EEF8F4",
            "icon": "⏳",
            "desc": "Rangkum peristiwa penting Perang Dunia II secara ringkas"
        },
        "Buat quiz tentang kimia": {
            "color": "#FCF4ED",
            "icon": "🧪",
            "desc": "Evaluasi kemampuan kimia Anda dengan latihan soal pilihan ganda"
        }
    }

    def get_card(label):
        return card_data.get(label, {
            "color": "#F0EBE3",
            "icon": "✦",
            "desc": "Pelajari topik ini bersama ScholarBot"
        })

    greeting = f"Halo, {user_name}!" if user_name else "Halo!"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            :root {{
                --color-background: #FAF6F0;
                --color-surface: #F5EFEB;
                --color-surface-raised: #FDFCFA;
                --color-walnut: #4A3728;
                --color-text-primary: #1C1814;
                --color-text-muted: #8A7F74;
                --color-border: #EADFCF;
                --color-border-strong: #C5BAB0;
                --font-serif: 'DM Serif Display', Georgia, serif;
                --font-sans: 'DM Sans', system-ui, sans-serif;
                --transition-base: 0.15s ease;
            }}

            body {{
                font-family: var(--font-sans);
                background: var(--color-background);
                margin: 0;
                padding: 0;
            }}

            .welcome-container {{
                max-width: 800px;
                margin: 0 auto;
                padding: 60px 24px 40px;
                text-align: center;
            }}

            .welcome-title {{
                font-size: 2.25rem;
                font-weight: 400;
                color: var(--color-text-primary);
                font-family: var(--font-serif);
                margin-bottom: 16px;
                line-height: 1.15;
                letter-spacing: -0.03em;
                animation: fadeInUp 0.6s ease;
            }}

            .welcome-sub {{
                color: var(--color-text-muted);
                font-size: 0.9375rem;
                line-height: 1.75;
                font-family: var(--font-sans);
                font-style: italic;
                max-width: 440px;
                margin: 0 auto 32px;
                animation: fadeInUp 0.6s ease 0.1s backwards;
            }}

            .welcome-divider {{
                width: 32px;
                height: 2px;
                background: var(--color-walnut);
                border-radius: 1px;
                margin: 0 auto 40px;
                opacity: 0.30;
                animation: fadeInUp 0.6s ease 0.2s backwards;
            }}

            /* Card Grid */
            .cards-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 16px;
                max-width: 720px;
                margin: 0 auto 32px;
                text-align: left;
            }}

            .topic-card {{
                background: var(--color-surface-raised);
                border: 1px solid var(--color-border);
                border-radius: 16px;
                padding: 20px;
                cursor: pointer;
                transition: all var(--transition-base);
                display: flex;
                align-items: center;
                gap: 16px;
                animation: fadeInUp 0.6s ease backwards;
            }}

            .topic-card:nth-child(1) {{ animation-delay: 0.3s; }}
            .topic-card:nth-child(2) {{ animation-delay: 0.35s; }}
            .topic-card:nth-child(3) {{ animation-delay: 0.4s; }}
            .topic-card:nth-child(4) {{ animation-delay: 0.45s; }}

            .topic-card:hover {{
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                border-color: var(--color-border-strong);
                transform: translateY(-2px);
            }}

            .topic-card:active {{
                transform: translateY(0);
            }}

            .card-icon {{
                width: 64px;
                height: 64px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 28px;
                flex-shrink: 0;
            }}

            .card-content {{
                flex: 1;
                min-width: 0;
            }}

            .card-title {{
                font-size: 16px;
                font-weight: 600;
                color: var(--color-text-primary);
                margin-bottom: 6px;
                font-family: var(--font-sans);
            }}

            .card-desc {{
                font-size: 13px;
                color: var(--color-text-muted);
                line-height: 1.5;
                font-family: var(--font-sans);
            }}

            .card-arrow {{
                font-size: 20px;
                color: var(--color-text-muted);
                flex-shrink: 0;
            }}

            /* Quick Action Bar */
            .quick-actions {{
                max-width: 720px;
                margin: 0 auto 32px;
                text-align: left;
            }}

            .quick-actions-label {{
                font-size: 16px;
                font-weight: 600;
                color: var(--color-text-primary);
                margin-bottom: 12px;
                font-family: var(--font-sans);
                animation: fadeInUp 0.6s ease 0.5s backwards;
            }}

            .quick-actions-row {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                animation: fadeInUp 0.6s ease 0.55s backwards;
            }}

            .quick-action-btn {{
                background: #1A1814;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-family: var(--font-sans);
                cursor: pointer;
                transition: all var(--transition-base);
                display: flex;
                align-items: center;
                gap: 8px;
            }}

            .quick-action-btn:hover {{
                background: #2A2420;
                transform: translateY(-1px);
            }}

            .quick-action-btn:active {{
                transform: translateY(0);
            }}

            /* Input Bar */
            .input-bar {{
                max-width: 720px;
                margin: 0 auto;
                background: var(--color-surface-raised);
                border: 1px solid var(--color-border);
                border-radius: 24px;
                padding: 14px 20px;
                display: flex;
                align-items: center;
                gap: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                animation: fadeInUp 0.6s ease 0.6s backwards;
            }}

            .input-icon {{
                font-size: 20px;
                color: var(--color-text-muted);
            }}

            .input-field {{
                flex: 1;
                border: none;
                background: transparent;
                font-size: 14px;
                color: var(--color-text-primary);
                font-family: var(--font-sans);
                outline: none;
            }}

            .input-field::placeholder {{
                color: var(--color-text-muted);
            }}

            .send-btn {{
                width: 36px;
                height: 36px;
                border-radius: 50%;
                background: #1A1814;
                border: none;
                color: white;
                font-size: 18px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all var(--transition-base);
            }}

            .send-btn:hover {{
                background: #2A2420;
                transform: scale(1.05);
            }}

            .send-btn:active {{
                transform: scale(0.95);
            }}

            @keyframes fadeInUp {{
                from {{
                    opacity: 0;
                    transform: translateY(20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}

            @media (max-width: 768px) {{
                .welcome-container {{
                    padding: 40px 16px 32px;
                }}

                .welcome-title {{
                    font-size: 1.75rem;
                }}

                .cards-grid {{
                    grid-template-columns: 1fr;
                    max-width: 100%;
                }}

                .quick-actions-row {{
                    flex-direction: column;
                }}

                .quick-action-btn {{
                    width: 100%;
                    justify-content: center;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="welcome-container">
            <div class="welcome-title">ScholarBot</div>
            <div class="welcome-sub">
                {greeting} Asisten belajar yang membantu memahami materi,
                membuat rangkuman, dan latihan soal.
            </div>
            <div class="welcome-divider"></div>

            <!-- Topic Cards Grid -->
            <div class="cards-grid">
                {"".join(f'''
                <div class="topic-card">
                    <div class="card-icon" style="background: {get_card(label)["color"]};">
                        {get_card(label)["icon"]}
                    </div>
                    <div class="card-content">
                        <div class="card-title">{label}</div>
                        <div class="card-desc">{get_card(label)["desc"]}</div>
                    </div>
                    <div class="card-arrow">›</div>
                </div>
                ''' for label, _ in suggestion_chips)}
            </div>

            <!-- Quick Action Bar -->
            <div class="quick-actions">
                <div class="quick-actions-label">Aksi Cepat</div>
                <div class="quick-actions-row">
                    {"".join(f'''
                    <button class="quick-action-btn">
                        <span>{get_card(label)["icon"]}</span>
                        <span>{label}</span>
                    </button>
                    ''' for label, _ in suggestion_chips)}
                </div>
            </div>

            <!-- Input Bar (Visual Only) -->
            <div class="input-bar">
                <div class="input-icon">✦</div>
                <input type="text" class="input-field" placeholder="Tanyakan sesuatu..." disabled>
                <button class="send-btn">→</button>
            </div>
        </div>
    </body>
    </html>
    """

    components.html(html, height=750)
