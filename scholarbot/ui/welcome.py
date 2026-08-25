"""Welcome screen rendering for ScholarBot.

Native Streamlit implementation with premium warm beige/cream styling,
matching the minimalist mockup exactly.
"""

import streamlit as st
try:
    from ui.icons import ICONS
except ModuleNotFoundError:
    try:
        from scholarbot.ui.icons import ICONS
    except ModuleNotFoundError:
        try:
            from .icons import ICONS
        except ImportError:
            import importlib
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            importlib.invalidate_caches()
            from icons import ICONS

def render_native_welcome(user_name: str = ""):
    """Renders a premium, minimalist, AI-native welcome screen."""
    import os
    import shutil
    
    # ─── Automatic file relocation of Tampilan.png to assets/mascot.png ───
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    src_path = os.path.join(root_dir, "Tampilan.png")
    dest_dir = os.path.join(os.path.dirname(current_dir), "assets")
    dest_path = os.path.join(dest_dir, "mascot.png")
    
    if os.path.exists(src_path):
        try:
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy(src_path, dest_path)
            os.remove(src_path)
        except Exception:
            pass

    greeting = f"Halo, {user_name}!" if user_name else "Halo!"
    
    # 1. Header Section (Title + Description + Robot Mascot Illustration)
    # Using columns to place text on left, and the beautifully designed robot mascot SVG on the right
    col1, col2 = st.columns([7, 3])
    
    with col1:
        st.markdown(f"""<div class="welcome-text-container">
<h1 class="welcome-title">Mau belajar apa hari ini?</h1>
<p class="welcome-desc">
    ScholarBot siap membantu memahami materi, membuat rangkuman, dan latihan soal.
</p>
</div>""", unsafe_allow_html=True)
        
    with col2:
        # Check if 3D mascot image exists in workspace assets or search paths
        img_path = None
        for p in [
            "scholarbot/assets/mascot.png", 
            "assets/mascot.png", 
            "../assets/mascot.png", 
            "Tampilan.png", 
            "scholarbot/Tampilan.png", 
            "../Tampilan.png", 
            "scholarbot/Logo.png", 
            "Logo.png", 
            "../Logo.png"
        ]:
            if os.path.exists(p):
                img_path = p
                break
                
        if img_path:
            # Render the gorgeous 3D mascot image beautifully styled with rounded corners!
            try:
                st.image(img_path, use_container_width=True)
            except TypeError:
                st.image(img_path, use_column_width=True)
        else:
            # Load the robot mascot SVG from assets/icons/mascot.svg or use a fallback
            try:
                with open("scholarbot/assets/icons/mascot.svg", "r") as f:
                    mascot_svg = f.read()
            except FileNotFoundError:
                # Inline fallback minimalist Mascot SVG
                mascot_svg = """
<svg viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 100%; height: auto; max-height: 160px;">
    <circle cx="100" cy="100" r="60" fill="#FDFCFA" stroke="#4A3728" stroke-width="3"/>
    <path d="M 80 85 Q 85 95 90 85" stroke="#4A3728" stroke-width="3" stroke-linecap="round" fill="none"/>
    <path d="M 110 85 Q 115 95 120 85" stroke="#4A3728" stroke-width="3" stroke-linecap="round" fill="none"/>
    <path d="M 85 110 Q 100 120 115 110" stroke="#4A3728" stroke-width="3" stroke-linecap="round" fill="none"/>
    <rect x="70" y="140" width="60" height="45" rx="3" fill="#EDE7D9" stroke="#4A3728" stroke-width="2"/>
    <line x1="100" y1="140" x2="100" y2="185" stroke="#4A3728" stroke-width="2"/>
</svg>
"""
            st.markdown(f'<div class="mascot-container">{mascot_svg}</div>', unsafe_allow_html=True)
        
    # 2. "Lanjutkan Belajar" Section
    st.markdown('<h2 class="section-title">Lanjutkan Belajar</h2>', unsafe_allow_html=True)
    
    # 3 Columns for the beautiful visual progress cards
    card_cols = st.columns(3)
    
    # Fetch user history topics
    topics = st.session_state.get("topics_discussed", [])
    display_topics = topics[-3:]
    display_topics.reverse() # Most recent first
    
    defaults = [
        {"title": "Machine Learning Basics", "icon": "brain", "progress": 78, "time": "2 jam lalu"},
        {"title": "Kimia: Stoikiometri", "icon": "flask", "progress": 45, "time": "kemarin"},
        {"title": "Perang Dunia II", "icon": "globe", "progress": 60, "time": "3 hari lalu"}
    ]
    
    cards_data = []
    icon_choices = ["brain", "flask", "globe", "graduation"]
    
    for i in range(3):
        if i < len(display_topics):
            topic = display_topics[i]
            short_topic = topic[:22] + "..." if len(topic) > 22 else topic
            progress = (len(topic) * 17 % 60) + 30 
            icon = icon_choices[len(topic) % len(icon_choices)]
            cards_data.append({"title": short_topic, "icon": icon, "progress": progress, "time": "Baru saja"})
        else:
            cards_data.append(defaults[i])

    for i, data in enumerate(cards_data):
        with card_cols[i]:
            icon_svg = ICONS.get(data['icon'], ICONS.get("graduation", ""))
            card_html = f"""<div class="learning-card">
<div class="card-header">
<div class="card-icon-wrapper {data['icon']}">
{icon_svg}
</div>
<div class="card-info">
<div class="card-subject">{data['title']}</div>
<div class="card-progress-text">{data['progress']}%</div>
</div>
</div>
<div class="card-progress-bar">
<div class="card-progress-fill" style="width: {data['progress']}%;"></div>
</div>
<div class="card-footer">Terakhir dipelajari {data['time']}</div>
</div>"""
            st.markdown(card_html.replace("\n", " ").strip(), unsafe_allow_html=True)

    st.markdown('<div class="welcome-spacer"></div>', unsafe_allow_html=True)
