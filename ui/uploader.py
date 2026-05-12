"""Document uploader UI component for RAG features.

Pure UI helpers — no Streamlit widget instantiation.
Widget calls are made by the caller (app.py) using config returned here.

Phase v3: Lightweight Educational RAG Edition.
"""

from typing import Callable

# ─── Section label ─────────────────────────────────────────────────────────────

RAG_SECTION_LABEL = "📄 Upload Materi"
CLEAR_DOCS_LABEL = "🗑️ Hapus Dokumen"

# Allowed file types
ALLOWED_EXTENSIONS = [".txt", ".pdf"]

# ─── UI Config Builder ─────────────────────────────────────────────────────────


def uploader_config() -> dict:
    """Return uploader widget configuration.

    Caller (app.py) uses this dict to call st.* widgets.

    Returns:
        Dict with widget metadata (no st. calls).
    """
    return {
        "section_label": RAG_SECTION_LABEL,
        "accepted_types": ALLOWED_EXTENSIONS,
        "clear_label": CLEAR_DOCS_LABEL,
        "max_file_size_mb": 10,
        "max_files": 5,
    }


# ─── Upload Result Display ─────────────────────────────────────────────────────


def build_upload_status_html(uploaded_docs: list[dict]) -> str:
    """Build HTML for upload status card.

    Args:
        uploaded_docs: List of {"filename": str, "size": int, "type": str}

    Returns:
        HTML string for status display.
    """
    if not uploaded_docs:
        return (
            '<div style="font-size:0.75rem;color:#718096;padding:4px 0 8px;">'
            'Belum ada dokumen. Upload materi belajar untuk memulai RAG.'
            '</div>'
        )

    html = '<div class="memory-item">'
    html += '<div class="memory-dot" style="background:#68d391"></div>'
    html += f'<span>📄 {len(uploaded_docs)} dokumen loaded</span></div>'

    for doc in uploaded_docs[:5]:
        fname = doc.get("filename", "unknown")
        size_kb = doc.get("size", 0) // 1024
        # Truncate long filenames
        if len(fname) > 25:
            fname = fname[:22] + "..."
        html += (
            f'<div class="memory-item" style="padding-left:20px;font-size:0.7rem;color:#a0aec0;">'
            f'• {fname} ({size_kb} KB)'
            f'</div>'
        )

    if len(uploaded_docs) > 5:
        html += (
            f'<div style="font-size:0.7rem;color:#718096;padding-left:20px;">'
            f'...dan {len(uploaded_docs) - 5} lagi'
            f'</div>'
        )

    return html


def build_upload_error_html(error_msg: str) -> str:
    """Build HTML for upload error message.

    Args:
        error_msg: Error description string

    Returns:
        HTML string.
    """
    return (
        f'<div style="font-size:0.75rem;color:#fc8181;padding:4px 0 8px;">'
        f'⚠️ {error_msg}'
        f'</div>'
    )


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename.

    Args:
        filename: Original filename

    Returns:
        Extension without dot, lowercase (e.g., "txt", "pdf")
    """
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def format_file_size(size_bytes: int) -> str:
    """Human-readable file size.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted string like "12 KB" or "1.2 MB"
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes // 1024} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
