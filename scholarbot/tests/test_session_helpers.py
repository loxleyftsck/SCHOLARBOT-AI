"""Tests for core/session_helpers.py — prompt building and intent detection."""

import pytest
from core.session_helpers import (
    detect_intent,
    build_system_prompt,
    build_messages,
    expand_short_command,
    is_quiz_request,
    extract_topic,
    extract_question_from_response,
    extract_answer_from_response,
    validate_payload,
)


class TestIntentDetection:
    """Test short command intent detection."""

    def test_give_answer_intents(self):
        """Should detect 'give answer' commands."""
        assert detect_intent("jawab") == "give_answer"
        assert detect_intent("jawaban dong") == "give_answer"
        assert detect_intent("yang jawabannya") == "give_answer"

    def test_give_explanation_intents(self):
        """Should detect 'give explanation' commands."""
        assert detect_intent("jelaskan") == "give_explanation"
        assert detect_intent("pembahasan dong") == "give_explanation"

    def test_continue_intents(self):
        """Should detect continue/acknowledge commands."""
        assert detect_intent("gas") == "continue"
        assert detect_intent("oke") == "acknowledge"
        assert detect_intent("ya") == "acknowledge"

    def test_hint_intents(self):
        """Should detect hint commands."""
        assert detect_intent("hint") == "give_hint"
        assert detect_intent("tolong") == "give_hint"
        assert detect_intent("gimana dong") == "give_hint"

    def test_new_question_intents(self):
        """Should detect new question commands."""
        assert detect_intent("buat lagi") == "new_question"
        assert detect_intent("yang lain") == "new_question"

    def test_normal_question_returns_none(self):
        """Normal questions should return None (no short command)."""
        assert detect_intent("jelaskan teori relativitas Einstein") is None
        assert detect_intent("apa itu machine learning") is None


class TestBuildSystemPrompt:
    """Test system prompt building."""

    def test_basic_prompt(self):
        """Should build a basic system prompt."""
        prompt = build_system_prompt(
            personality_key="Tutor Ramah",
            user_name="Andi",
            topics=["fisika", "matematika"],
        )
        assert len(prompt) > 50
        assert "Andi" in prompt

    def test_prompt_includes_personality(self):
        """Should include personality traits in prompt."""
        prompt = build_system_prompt(personality_key="Tutor Ramah")
        # Should contain at least some of the personality system prompt
        assert len(prompt) > 100

    def test_prompt_includes_topics(self):
        """Should include topics in prompt."""
        prompt = build_system_prompt(
            personality_key="Tutor Ramah",
            topics=["fisika kuantum", "termodinamika"],
        )
        assert "fisika kuantum" in prompt or "termodinamika" in prompt

    def test_quiz_context_injected(self):
        """Should inject quiz context when active."""
        prompt = build_system_prompt(
            personality_key="Tutor Ramah",
            current_context="quiz",
            last_question="Apa rumus luas lingkaran?",
        )
        assert "quiz" in prompt.lower() or "kuis" in prompt.lower()


class TestBuildMessages:
    """Test message list building."""

    def test_includes_system_message(self):
        """Should start with system message."""
        messages = build_messages(
            personality_key="Tutor Ramah",
            user_name="Andi",
            topics=[],
            conversation_history=[],
        )
        assert messages[0]["role"] == "system"
        assert isinstance(messages[0]["content"], str)

    def test_includes_conversation_history(self):
        """Should include conversation history."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        messages = build_messages(
            personality_key="Tutor Ramah",
            user_name="Andi",
            topics=[],
            conversation_history=history,
        )
        # Should have: system + user + assistant
        assert len(messages) == 3
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"

    def test_strips_time_metadata_from_history(self):
        """Should strip time/id from conversation history."""
        history = [
            {"role": "user", "content": "Hello", "time": "12:00", "id": "msg-1"},
        ]
        messages = build_messages(
            personality_key="Tutor Ramah",
            user_name="Andi",
            topics=[],
            conversation_history=history,
        )
        # Should NOT have 'time' or 'id' in messages list
        for msg in messages:
            assert "time" not in msg
            assert "id" not in msg


class TestQuizDetection:
    """Test quiz request detection."""

    def test_quiz_keywords(self):
        """Should detect quiz-related keywords."""
        assert is_quiz_request("buatin soal matematika") is True
        assert is_quiz_request("tanya dong") is True

    def test_non_quiz_requests(self):
        """Should return False for non-quiz requests."""
        assert is_quiz_request("jelaskan fisika") is False
        assert is_quiz_request("apa itu AI") is False


class TestExpandShortCommand:
    """Test short command expansion."""

    def test_expand_answer_command(self):
        """Should expand 'give answer' with previous context."""
        result = expand_short_command(
            "jawab dong",
            last_question="Apa itu fotosintesis?",
            last_answer="Fotosintesis adalah...",
        )
        assert len(result) > 20  # Should be expanded
        assert "fotosintesis" in result.lower()

    def test_expand_hint_command(self):
        """Should expand hint command."""
        result = expand_short_command(
            "hint",
            last_question="Hitung integral dari x^2",
        )
        assert "integral" in result.lower() or "x^2" in result


class TestPayloadValidation:
    """Test message payload validation."""

    def test_valid_payload(self):
        """Valid payload should pass."""
        messages = [
            {"role": "system", "content": "You are a tutor."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        valid, error = validate_payload(messages)
        assert valid is True
        assert error == ""

    def test_invalid_role(self):
        """Invalid role should fail."""
        messages = [
            {"role": "system", "content": "You are a tutor."},
            {"role": "invalid_role", "content": "Hello"},
        ]
        valid, error = validate_payload(messages)
        assert valid is False
        assert "tidak dikenali" in error

    def test_empty_content_fails(self):
        """Empty content should fail."""
        messages = [
            {"role": "system", "content": "You are a tutor."},
            {"role": "user", "content": ""},
        ]
        valid, error = validate_payload(messages)
        assert valid is False
        assert "kosong" in error

    def test_wrong_role_alternation_fails(self):
        """Wrong role order should fail."""
        messages = [
            {"role": "system", "content": "You are a tutor."},
            {"role": "assistant", "content": "I speak first?"},  # Wrong! User should be first
            {"role": "user", "content": "Then user?"},
        ]
        valid, error = validate_payload(messages)
        assert valid is False
