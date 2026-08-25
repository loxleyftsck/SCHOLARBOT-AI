"""Document loader — extract text from TXT and PDF files.

Lightweight implementation with minimal dependencies.
- TXT: direct file reading with encoding detection
- PDF: PyPDF2 for extraction (fallback to pypdf)

No heavy document processing frameworks.
"""

import io
from typing import Optional


def extract_txt(file_bytes: bytes, filename: str = "") -> str:
    """Extract text from a TXT file.

    Handles encoding detection and fallbacks.

    Args:
        file_bytes: Raw file content as bytes
        filename: Original filename (for error messages)

    Returns:
        Extracted text content

    Raises:
        ValueError: If file is empty or text extraction fails
    """
    if not file_bytes:
        raise ValueError(f"File {filename} kosong.")

    # Try common encodings in order
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

    for encoding in encodings:
        try:
            text = file_bytes.decode(encoding)
            # Validate decoded text has reasonable content
            if len(text.strip()) > 10:
                return text
        except (UnicodeDecodeError, UnicodeError):
            continue

    # All encodings failed
    raise ValueError(f"Gagal decode file {filename}. Cek encoding file TXT.")


def extract_pdf(file_bytes: bytes, filename: str = "") -> str:
    """Extract text from a PDF file using PyPDF2.

    Args:
        file_bytes: Raw file content as bytes
        filename: Original filename (for error messages)

    Returns:
        Extracted text content (concatenated from all pages)

    Raises:
        ValueError: If PDF extraction fails or PyPDF2 not installed
    """
    try:
        import pypdf as pdf_lib
    except ImportError:
        try:
            import PyPDF2 as pdf_lib
        except ImportError:
            raise ValueError(
                "pypdf atau PyPDF2 belum terinstall. Install dengan: pip install pypdf\n"
                "Atau gunakan file TXT sebagai alternatif."
            )

    if not file_bytes:
        raise ValueError(f"File {filename} kosong.")

    try:
        # Create PDF reader from bytes
        pdf_file = io.BytesIO(file_bytes)
        reader = pdf_lib.PdfReader(pdf_file)

        # Validate PDF has pages
        if len(reader.pages) == 0:
            raise ValueError(f"PDF {filename} tidak memiliki halaman.")

        # Extract text from all pages
        text_parts = []
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_parts.append(page_text)
            except Exception as e:
                # Skip problematic pages but continue
                continue

        if not text_parts:
            raise ValueError(f"PDF {filename} tidak memiliki teks yang bisa diekstrak. "
                             "Mungkin PDF berupa gambar (scanned document).")

        return "\n\n".join(text_parts)

    except Exception as e:
        # Handle library-specific or general PDF read errors safely
        raise ValueError(f"Gagal ekstrak PDF {filename}: {e}")


def extract_document(file_bytes: bytes, filename: str, file_type: str) -> str:
    """Unified document extraction interface.

    Detects file type and routes to appropriate extractor.

    Args:
        file_bytes: Raw file content
        filename: Original filename
        file_type: File extension (e.g., "txt", "pdf")

    Returns:
        Extracted text content

    Raises:
        ValueError: If file type not supported or extraction fails
    """
    file_type = file_type.lower().lstrip('.')

    if file_type == 'txt':
        return extract_txt(file_bytes, filename)
    elif file_type == 'pdf':
        return extract_pdf(file_bytes, filename)
    else:
        raise ValueError(
            f"Tipe file '{file_type}' tidak didukung. "
            f"Gunakan .txt atau .pdf."
        )


# Metadata extraction helpers
def get_document_info(text: str, filename: str) -> dict:
    """Extract basic metadata from document text.

    Args:
        text: Extracted document text
        filename: Original filename

    Returns:
        Dict with metadata: char_count, word_count, line_count, filename
    """
    lines = text.split('\n')
    words = text.split()

    return {
        'filename': filename,
        'char_count': len(text),
        'word_count': len(words),
        'line_count': len(lines),
        'preview': text[:200].strip(),
    }
