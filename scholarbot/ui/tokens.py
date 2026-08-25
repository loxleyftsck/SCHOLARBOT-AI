"""Design tokens for ScholarBot AI — single source of truth for all visual decisions.

Editorial warm minimalism design system v3.
All CSS references these via CSS custom properties.
No hardcoded values in styles.py.
"""

# ─── Color Palette ──────────────────────────────────────────────────────────────

COLORS = {
    "editorial": {
        # ── Backgrounds ─────────────────────────────────────────
        "background":    "#FAF6F0",   # Warm cream — main canvas
        "surface":        "#F5EFEB",   # Card surface — sidebar, bubbles
        "surface_raised":  "#FDFCFA",   # Raised surface — input field, user bubble
        "surface_overlay":"#F5EFEB",   # Sidebar background
        # ── Accent — Dark Walnut ─────────────────────────────────
        "accent_dark":    "#2C2417",   # Dark walnut — active states, text on light bg
        "walnut":         "#4A3728",   # Walnut — bot avatar, send button
        "walnut_light":   "#5C4535",   # Lighter walnut — hover states
        "walnut_muted":   "#7A6250",   # Muted — typing dots, dividers
        # ── Accent — Warm Gold ──────────────────────────────────
        "primary":        "#8B6914",   # Deep gold — focus ring, primary CTA
        "primary_dark":   "#6D5010",   # Darker gold — pressed CTA
        "primary_light":   "#C49A3A",   # Lighter gold — hover CTA
        "accent_warm":    "#8B6B3D",   # Warm accent — links, subtle highlights
        # ── Semantic ────────────────────────────────────────────
        "secondary":      "#4A7C6F",   # Sage green — success indicators
        "warning":        "#C49A3A",   # Warm amber — warning
        "error":          "#A84040",   # Muted red — error states
        "info":           "#4A6B8A",   # Muted blue — info
        # ── Text ────────────────────────────────────────────────
        "text_primary":   "#1C1814",   # Near-black — headings, primary text
        "text_body":      "#3D3632",   # Warm dark gray — body text, labels
        "text_muted":     "#8A7F74",   # Warm medium gray — captions, meta
        "text_subtle":    "#B5A99E",   # Warm light gray — placeholders, timestamps
        "text_on_dark":   "#F5F0E8",   # Light text on walnut/accent_dark bg
        # ── Borders ────────────────────────────────────────────
        "border":         "#EADFCF",   # Subtle warm border — cards, inputs (lighter)
        "border_strong":  "#C5BAB0",   # Stronger border — hover, focus
        "divider":        "#EAE2D8",   # Section divider — sidebar headers
        "outline_focus":  "#8B6914",   # Focus ring — keyboard nav (gold)
    },
}

# ─── Typography ─────────────────────────────────────────────────────────────────

FONTS = {
    "editorial": {
        # Serif — bot messages, welcome title, section headings
        "serif":   "'DM Serif Display', Georgia, serif",
        # Sans — UI chrome: labels, buttons, inputs, timestamps, user bubbles
        "sans":    "'DM Sans', system-ui, sans-serif",
        # Mono — code blocks only
        "mono":    "'JetBrains Mono', Consolas, monospace",
    },
}

# ─── Font Sizes (8px type scale) ───────────────────────────────────────────────
# 12 / 14 / 16 / 18 / 22 / 28 / 36 / 48 / 64

FONT_SIZES = {
    "2xs":  "0.625rem",   # 10px — timestamps (subtle)
    "xs":   "0.6875rem",  # 11px — meta, captions
    "sm":   "0.75rem",    # 12px — sidebar labels, mode buttons
    "base": "0.875rem",  # 14px — body text, user bubbles, chat messages
    "md":   "0.9375rem",  # 15px — welcome subhead
    "lg":   "1rem",       # 16px — sidebar inputs
    "xl":   "1.125rem",   # 18px — bot message
    "2xl":  "1.375rem",   # 22px — section headings
    "3xl":  "1.75rem",    # 28px — welcome title mobile
    "4xl":  "2.25rem",    # 36px — welcome title desktop
}

# ─── Line Heights ───────────────────────────────────────────────────────────────

LINE_HEIGHTS = {
    "tight":  "1.2",    # Headings, titles
    "snug":   "1.4",    # Labels, buttons, UI text
    "base":   "1.6",    # Body text
    "relaxed":"1.75",   # Bot messages, welcome sub
}

# ─── Letter Spacing ─────────────────────────────────────────────────────────────

LETTER_SPACING = {
    "tight":  "-0.02em",  # Headings
    "normal": "0",        # Body
    "wide":   "0.02em",   # Medium emphasis
    "wider":  "0.06em",   # All-caps labels
    "widest": "0.12em",   # ALL-CAPS LABELS
}

# ─── Spacing (8px grid, strict) ────────────────────────────────────────────────
# Tokens: space-1=4, space-2=8, space-3=12, space-4=16, space-5=20,
#         space-6=24, space-8=32, space-10=40, space-12=48, space-16=64

SPACING = {
    "1":  "4px",
    "2":  "8px",
    "3":  "12px",
    "4":  "16px",
    "5":  "20px",
    "6":  "24px",
    "7":  "28px",
    "8":  "32px",
    "10": "40px",
    "12": "48px",
    "16": "64px",
    "20": "80px",
}

# ─── Border Radius (8px grid) ───────────────────────────────────────────────────

RADIUS = {
    "sm":   "4px",    # Small chips: input focus, sidebar widgets
    "md":   "8px",    # Medium: cards, avatar, sidebar widgets
    "lg":   "12px",   # Large: message bubbles, chips
    "xl":   "16px",   # Extra large: chat input bar
    "pill": "20px",   # Pill: suggestion chips
    "full":"9999px",  # Full round: mode indicators
}

# ─── Shadows (subtle, no glow) ────────────────────────────────────────────────────
# Editorial principle: shadows earn their keep — depth through layering, not drama.

SHADOWS = {
    "none":  "none",
    "sm":    "0 1px 3px rgba(44,36,23,0.05), 0 1px 2px rgba(44,36,23,0.03)",
    "md":    "0 2px 8px rgba(44,36,23,0.07), 0 1px 3px rgba(44,36,23,0.04)",
    "lg":    "0 4px 16px rgba(44,36,23,0.09), 0 2px 6px rgba(44,36,23,0.05)",
}

# ─── Transitions (0.15s ease as standard) ────────────────────────────────────────

TRANSITIONS = {
    "fast":   "0.10s ease",
    "base":   "0.15s ease",
    "normal": "0.20s ease",
    "slow":   "0.30s ease",
}

# ─── Z-Index ────────────────────────────────────────────────────────────────────

Z_INDEX = {
    "base":    0,
    "raised":  10,
    "sticky":  50,
    "overlay": 100,
    "modal":   200,
}

# ─── Layout ────────────────────────────────────────────────────────────────────

LAYOUT = {
    "content_max_width": "720px",
    "sidebar_width":     "260px",
    "chat_max_width":   "660px",
}

# ─── Avatar Sizes ───────────────────────────────────────────────────────────────

AVATAR_SIZE = {
    "sm": "28px",
    "md": "32px",
    "lg": "40px",
}

# ─── Active Theme ──────────────────────────────────────────────────────────────

ACTIVE_THEME = "editorial"
ACTIVE_FONTS = "editorial"

# ─── Convenience Accessors ──────────────────────────────────────────────────────


def get_colors():
    return COLORS[ACTIVE_THEME]


def get_fonts():
    return FONTS[ACTIVE_FONTS]


def build_css_variables() -> str:
    """Build a CSS :root block with all design tokens as custom properties."""
    c = get_colors()
    f = get_fonts()

    vars = []
    # Colors
    for key, val in c.items():
        vars.append(f"  --color-{key}: {val};")
    # Fonts
    for key, val in f.items():
        vars.append(f"  --font-{key}: {val};")
    # Font sizes
    for key, val in FONT_SIZES.items():
        vars.append(f"  --text-{key}: {val};")
    # Spacing
    for key, val in SPACING.items():
        vars.append(f"  --space-{key}: {val};")
    # Radius
    for key, val in RADIUS.items():
        vars.append(f"  --radius-{key}: {val};")
    # Shadows
    for key, val in SHADOWS.items():
        vars.append(f"  --shadow-{key}: {val};")
    # Transitions
    for key, val in TRANSITIONS.items():
        vars.append(f"  --transition-{key}: {val};")
    # Layout
    for key, val in LAYOUT.items():
        vars.append(f"  --layout-{key}: {val};")
    # Avatar
    for key, val in AVATAR_SIZE.items():
        vars.append(f"  --avatar-{key}: {val};")

    return ":root {\n" + "\n".join(vars) + "\n}"