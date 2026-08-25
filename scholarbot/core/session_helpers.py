"""Prompt builder and conversation utilities — no Streamlit deps.

Extracted from app.py Phase 3 refactor.
Responsibility: build LLM inputs (messages, system prompt, topic extraction).
Intent detection for short commands.
"""

import re
from prompts import PERSONALITIES

# Default model (can be overridden via set_model in llm_client, or here)
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048

# ─── Short Command Intent Detection ─────────────────────────────────────────────

# Pattern: short single-word or two-word commands
# These are treated as follow-up commands, not fresh queries
SHORT_COMMAND_PATTERNS = {
    # "Give answer" group
    r"^(gas|lanjut(kan)?|next|lanjut dong)$": "continue",
    r"^(jawab|jwbn|jawaban|jwb)(\s+dong)?$": "give_answer",
    r"^berikan\s*($|jawabannya?|jawaban dong)": "give_answer",
    r"^yang\s*($|jawabannya)": "give_answer",
    # "Give explanation" group
    r"^(bahas|pembahasan|jelaskan|penjelasan|cara)($|\s)": "give_explanation",
    r"^pembahasannya?\s*dong$": "give_explanation",
    # "Generate new question" group
    r"^(buat\s*lagi|soal\s*baru|new|ulangi)$": "new_question",
    r"^yang\s*lain$": "new_question",
    # "Give hint" group
    r"^(hint|tolong|tips)$": "give_hint",
    r"^bantu(an)?$": "give_hint",
    r"^gimana\s*($|dong)": "give_hint",
    # "Continue/continue" group
    r"^(terus|oke|ok|mau|yes|yeah|ya)$": "acknowledge",
    r"^(makasih|terima\s*kasih|thanks)$": "acknowledge",
    # "Show question" group
    r"^(soalnya?\s*(mana|di?\s*mana)|mana\s*soalnya?)$": "show_question",
}


def detect_intent(text: str) -> str | None:
    """Detect if user message is a short follow-up command.

    Args:
        text: Raw user message (already lowercased for matching)

    Returns:
        Intent key or None if it's a fresh query.
    """
    text = text.strip().lower()
    # Strict threshold: 4 words max for short command classification
    # This prevents "jelaskan teori X" (fresh query) from being treated as short command
    if len(text.split()) > 3:
        return None  # Not a short command, likely a fresh query

    for pattern, intent in SHORT_COMMAND_PATTERNS.items():
        if re.search(pattern, text):
            return intent
    return None


# Intent → expanded prompt that gets prepended before the short command
INTENT_EXPANSIONS = {
    "continue": (
        "Lanjutkan aktivitas terakhir yang sedang kita kerjakan. "
        "Jika soal sudah dibuat, lanjutkan dengan aktivitas berikutnya."
    ),
    "give_answer": (
        "User meminta jawaban dari soal yang terakhir dibuat. "
        "Berikan langsung jawabannya tanpa basa-basi."
    ),
    "give_explanation": (
        "User meminta pembahasan dari soal yang terakhir dibuat. "
        "Jelaskan langkah demi langkah dengan detail."
    ),
    "new_question": (
        "User meminta soal baru dengan topik yang sama atau mirip "
        "dengan soal terakhir yang sudah dibuat."
    ),
    "give_hint": (
        "User meminta hint/tips untuk soal terakhir. "
        "Berikan petunjuk yang membantu tanpa langsung memberi jawaban."
    ),
    "acknowledge": (
        "User merespons dengan affirmasi. "
        "Konfirmasi dengan singkat dan tanyakan apakah ingin lanjut."
    ),
    "show_question": (
        "User meminta untuk melihat ulang soal terakhir."
    ),
}


def expand_short_command(text: str, last_question: str = "", last_answer: str = "",
                          current_context: str = "") -> str:
    """Expand a short command by injecting conversation context.

    If the message is a short follow-up command, prepend context
    from the last question/answer so the LLM knows what it's referring to.

    Args:
        text: Raw user message
        last_question: Last question stored in session
        last_answer: Last answer stored in session
        current_context: Current context ("quiz", "tutor", etc.)

    Returns:
        Expanded message ready to send to LLM.
    """
    text_lower = text.strip().lower()
    intent = detect_intent(text_lower)

    if intent is None:
        return text  # Fresh query, send as-is

    expansion = INTENT_EXPANSIONS.get(intent, "")

    # Build context block
    context_parts = []

    if last_question:
        context_parts.append(f"[KONTEKS SOAL TERAKHIR]: {last_question}")
        if last_answer and intent == "give_answer":
            context_parts.append(f"[KONTEKS JAWABAN TERAKHIR]: {last_answer}")

    if context_parts:
        context_block = "\n".join(context_parts)
        return (
            f"{expansion}\n\n{context_block}\n\n"
            f"[Pesan user]: {text}\n\n"
            "TANGGAPI pesan user dengan tepat berdasarkan konteks di atas."
        )

    # No last_question stored, but we have intent — still add expansion
    return f"{expansion}\n\n[Pesan user]: {text}"


# Extract answer from bot response (for storage in last_answer)
QUIZ_ANSWER_PATTERNS = [
    r"(?:Jawaban(?:nya)?|Kunci Jawaban|Jawabannya?)\s*[:\-]?\s*([^\n]+(?:\n[^\n]+)*)",
    r"(?:Jawaban benar(?:nya)?|Jawab(?:an)?\s*(?:yang\s*)?benar)\s*[:\-]?\s*([^\n]+)",
    r"(?:Opsi\s+[A-D][:\-)])\s*([^\n]+)",
]
QUIZ_ANSWER_RE = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in QUIZ_ANSWER_PATTERNS]


def extract_answer_from_response(response: str) -> str:
    """Extract answer from bot's quiz generation response.

    Tries multiple patterns to find the answer key.
    Returns the first match found, or empty string.
    """
    if not response:
        return ""

    # Try numbered answer list (e.g. "1. A  2. B  3. C")
    numbered = re.search(
        r"(?:Jawaban(?:nya)?|Kunci)\s*[:\-]?\s*"
        r"((?:\d+[\.\)]\s*[A-D](?:\s*,\s*\d+[\.\)]\s*[A-D])*|\n\d+[\.\)]\s*[A-D].*?))",
        response,
        re.IGNORECASE
    )
    if numbered:
        return numbered.group(0).strip()

    for pattern in QUIZ_ANSWER_RE:
        m = pattern.search(response)
        if m:
            return m.group(0).strip()

    return ""


# Extract question from bot's quiz generation response
def extract_question_from_response(response: str) -> str:
    """Extract question text from bot's quiz generation response.

    Returns first ~200 chars of the question section, or empty string.
    """
    if not response:
        return ""
    # Look for first question pattern
    m = re.search(
        r"(?:Soal\s*\d+[:\.\)]?\s*(.{10,200}?)(?=\n\n|\nSoal|\nPembahasan|\Z))",
        response,
        re.IGNORECASE | re.DOTALL
    )
    if m:
        return m.group(1).strip()
    # Fallback: first 200 chars
    return response[:200].strip()


# Detect if the last user message was a quiz generation request
QUIZ_REQUEST_PATTERNS = [
    r"(?:buatkan?\s*)?(?:soal|quiz|kuis)(?:\s+\w+)*",
    r"^(?:buatkan?|buat|lg|lagi)\s*(?:soalnya?|quiz)",
    r"(?:tanya|tanyakan?)(?:\s+\w+)*",
]


def is_quiz_request(text: str) -> bool:
    """Check if user message is a quiz/question generation request."""
    text_lower = text.lower().strip()
    for pattern in QUIZ_REQUEST_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


# ─── System Prompt Building ────────────────────────────────────────────────────────

# Conversation continuity and short command handling rules
CONVERSATION_RULES = """

## CONVERSATION CONTINUITY
- PERTAHANKAN konteks percakapan sebelumnya dalam setiap respons
- Jangan pernah kehilangan topik yang sedang dibahas
- Jika user memberikan command pendek tanpa konteks jelas, selalu cek percakapan terakhir

## SHORT COMMAND HANDLING
- "gas" / "lanjut" / "next" → lanjutkan aktivitas terakhir (buat soal lagi, lanjut tutor, dll)
- "jawab" / "berikan jawabannya" → berikan jawaban dari soal/kuis terakhir yang kamu buat
- "bahas" / "pembahasan" / "jelaskan" → jelaskan pembahasan dari soal terakhir
- "buat lagi" / "soal baru" → buat lagi dengan topik yang sama atau mirip
- "hint" / "tolong" / "tips" → berikan petunjuk untuk soal terakhir tanpa langsung memberi jawaban

## RESPONSE STYLE
- SAAT user minta soal/kuis → LANGSUNG buat soal (tanpa pembukaan panjang seperti "Oke, saya akan...")
- SAAT user minta jawaban → LANGSUNG berikan jawaban yang diminta
- SAAT user minta pembahasan → LANGSUNG jelaskan
- To-the-point untuk command pendek, tidak perlu sapaan ulang setiap kali
"""[1:]  # Strip leading newline


def build_system_prompt(personality_key: str, user_name: str = "", topics: list[str] = None,
                       current_context: str = "", last_question: str = "") -> str:
    """Build system prompt by injecting personality + session memory + conversation rules.

    Args:
        personality_key: One of PERSONALITIES.keys()
        user_name: User's display name (optional)
        topics: List of recently discussed topic strings (optional)
        current_context: Current active context like "quiz" (optional)
        last_question: Last question generated for context injection (optional)

    Returns:
        Complete system prompt string.
    """
    # Fallback to default personality if key not found
    if personality_key not in PERSONALITIES:
        personality_key = "😊 Santai & Friendly"
    base = PERSONALITIES[personality_key]["system"]
    memory_parts = []
    if user_name:
        memory_parts.append(f"Nama user adalah {user_name}, sapa dengan namanya bila relevan.")
    if topics:
        recent = ", ".join(topics[-3:])
        memory_parts.append(f"Topik yang sudah dibahas sebelumnya: {recent}.")
    if memory_parts:
        base += " " + " ".join(memory_parts)
    base += (
        " Kamu fokus pada bidang edukasi dan pembelajaran. "
        "Saat user menanyakan hal di luar topik belajar, arahkan kembali dengan sopan. "
        "Selalu berikan jawaban yang akurat, bermanfaat, dan mendidik."
    )
    # Add conversation continuity rules
    base += CONVERSATION_RULES

    # Inject context awareness
    if current_context == "quiz" and last_question:
        base += f"\n\nSAAT INI dalam mode kuis/soal. Soal terakhir yang dibuat: {last_question[:200]}"

    return base


def build_messages(personality_key: str, user_name: str, topics: list[str],
                    conversation_history: list[dict],
                    current_context: str = "", last_question: str = "") -> list[dict]:
    """Assemble the full messages list: system + history.

    Args:
        personality_key: Personality mode key
        user_name: User's name
        topics: Topics list from session state
        conversation_history: List of {"role": ..., "content": ..., "time": ...}
        current_context: Current active context (e.g., "quiz", "tutor")
        last_question: Last question generated (for context injection)

    Returns:
        Messages list ready for Groq API.
    """
    system_content = build_system_prompt(
        personality_key, user_name, topics,
        current_context=current_context,
        last_question=last_question
    )
    messages = [{"role": "system", "content": system_content}]
    for m in conversation_history:
        role = "user" if m["role"] == "user" else "assistant"
        messages.append({"role": role, "content": m["content"]})
    return messages


def extract_topic(text: str) -> str | None:
    """Extract a short topic label from user input.

    Looks for trigger keywords and returns the 1–4 word phrase that follows.
    Falls back to full short input. Returns None for long inputs without triggers.

    Args:
        text: Raw user message

    Returns:
        Topic string or None.
    """
    lower_text = text.lower().strip()
    
    # Check if this is a pure meta-command (no academic topic content)
    meta_commands = ["mindmap", "mind map", "peta konsep", "buat jadi", "kuis", "soal", "latihan", "reactflow"]
    is_pure_meta = any(
        lower_text == cmd 
        or lower_text == f"buat {cmd}" 
        or lower_text == f"buatkan {cmd}" 
        or lower_text == f"buatkan saya {cmd}" 
        or lower_text == f"coba pakai {cmd}"
        or lower_text == f"tidak terjadi apa apa"
        for cmd in meta_commands
    )
    if is_pure_meta:
        return None

    # First attempt: Try extracting after dynamic trigger keywords
    keywords = ["tentang", "mengenai", "materi", "belajar", "pelajaran", "konsep", "jelaskan"]
    for kw in keywords:
        if kw in lower_text:
            idx = lower_text.find(kw) + len(kw)
            # Find in original case string to preserve title casing
            orig_idx = text.lower().find(kw) + len(kw)
            snippet = text[orig_idx:].strip().split()
            # Clean up trailing punctuation
            cleaned_words = []
            for word in snippet[0:4]:
                cleaned_word = word.rstrip(".,?!:;()")
                if cleaned_word:
                    cleaned_words.append(cleaned_word)
            if cleaned_words:
                return " ".join(cleaned_words)

    # Second attempt: Clean meta words and see if it's a short topic prompt
    # E.g. "buatkan mindmap Stoikiometri Kimia" -> "Stoikiometri Kimia"
    cleaned = text
    for word in ["buatkan saya", "buatkan", "buat", "coba pakai", "pendekatan", "reactflow", "mindmap", "mind map", "peta konsep", "kuis", "latihan"]:
        import re
        cleaned = re.sub(rf"\b{word}\b", "", cleaned, flags=re.IGNORECASE)
    
    cleaned = cleaned.strip()
    # Clean up trailing/leading punctuation
    cleaned = cleaned.strip(".,?!:;()")
    
    # If the remaining cleaned string is a short descriptive phrase, treat it as the topic
    if cleaned and len(cleaned) < 50 and len(cleaned.split()) <= 4:
        return cleaned

    # Fallback to short plain text input
    if len(text) < 50:
        return text.strip()
        
    return None


MAX_MESSAGE_PAIRS = 20  # strict context window cap


def validate_payload(messages: list[dict]) -> tuple[bool, str]:
    """Validate the messages payload before sending to the Groq API.

    Checks:
    - messages is a non-empty list
    - roles alternate user/assistant (or start with system)
    - no null / empty content in user or assistant messages
    - system prompt is a plain string, not an object

    Returns:
        (is_valid, error_message)
    """
    if not messages:
        return False, "Pesan kosong. Ketik pertanyaan terlebih dahulu."

    if len(messages) > MAX_MESSAGE_PAIRS * 2 + 1:
        # Hard cap — truncate to last N pairs
        messages = messages[:MAX_MESSAGE_PAIRS * 2 + 1]

    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            return False, f"Format pesan tidak valid di index {i}."

        role = msg.get("role", "")
        content = msg.get("content", "")

        if role not in ("system", "user", "assistant"):
            return False, f"Role tidak dikenali di index {i}: '{role}'."

        if role in ("user", "assistant"):
            if content is None:
                return False, f"Pesan di index {i} kosong."
            if not isinstance(content, str):
                return False, f"Pesan di index {i} harus teks."
            if content.strip() == "":
                return False, f"Pesan di index {i} kosong."

        if role == "system":
            if not isinstance(content, str):
                return False, "System prompt harus teks, bukan objek."

    # Check role alternation: after system, must be user, then assistant, then user...
    # Build stripped role list (no system)
    non_system_roles = [m["role"] for m in messages if m["role"] != "system"]

    # Find first non-system
    if non_system_roles:
        expected = "user"
        for r in non_system_roles:
            if r != expected:
                return False, (
                    "Urutan percakapan tidak valid. "
                    "Coba reset chat atau mulai topik baru."
                )
            expected = "assistant" if expected == "user" else "user"

    return True, ""


def call_llama(user_msg: str, personality_key: str, user_name: str,
               topics: list[str], conversation_history: list[dict],
               current_context: str = "", last_question: str = "",
               last_answer: str = "", retrieved_chunks: list = None) -> str:
    """High-level convenience function: build messages + call Groq.

    Detects short follow-up commands and expands them with conversation context.
    Auto-detects quiz requests and sets current_context="quiz".
    v3: Optional RAG context injection via retrieved_chunks.
    """
    from core.llm_client import chat
    from core.rag_context import build_rag_system_prompt, should_use_rag

    # Check if message is a short follow-up command
    intent = detect_intent(user_msg.lower().strip())
    if intent:
        # Short command — expand with conversation context before sending to LLM
        effective_msg = expand_short_command(
            user_msg, last_question, last_answer, current_context
        )
    else:
        effective_msg = user_msg

    # Auto-detect quiz request → set context to quiz
    detected_context = current_context
    if is_quiz_request(user_msg):
        detected_context = "quiz"

    # Build base system prompt
    base_system_prompt = build_system_prompt(
        personality_key, user_name, topics,
        current_context=detected_context,
        last_question=last_question
    )

    # v3 RAG: Inject document context if available and relevant
    retrieved_chunks = retrieved_chunks or []
    has_documents = bool(retrieved_chunks)
    if retrieved_chunks and should_use_rag(user_msg, has_documents=has_documents):
        system_content = build_rag_system_prompt(base_system_prompt, retrieved_chunks, detected_context)
    else:
        system_content = base_system_prompt

    messages = [{"role": "system", "content": system_content}]
    for m in conversation_history:
        role = "user" if m["role"] == "user" else "assistant"
        messages.append({"role": role, "content": m["content"]})
    # Add user message (effective_msg may be expanded for short commands)
    messages.append({"role": "user", "content": effective_msg})

    # Validate payload before sending
    valid, err_msg = validate_payload(messages)
    if not valid:
        return f"Terjadi kesalahan, coba lagi: {err_msg}"

    return chat(messages, DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS)