"""Tests for core/llm_client.py — streaming and non-streaming modes."""

import pytest
from unittest.mock import patch, MagicMock, Mock
from core.llm_client import (
    chat,
    stream_chat,
    _non_stream_chat,
    _stream_chat,
    _classify_error,
    set_api_key,
    MAX_RETRIES,
    BASE_DELAY,
)


class TestNonStreaming:
    """Test non-streaming chat completion."""

    def test_chat_returns_string(self):
        """Non-streaming should return a string."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello world"
        mock_client.chat.completions.create.return_value = mock_response

        with patch("core.llm_client.get_client", return_value=mock_client):
            result = chat([{"role": "user", "content": "hi"}])
            assert isinstance(result, str)
            assert result == "Hello world"

    def test_chat_empty_response_returns_error_message(self):
        """Empty response should return error message."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = []
        mock_client.chat.completions.create.return_value = mock_response

        with patch("core.llm_client.get_client", return_value=mock_client):
            result = chat([{"role": "user", "content": "hi"}])
            assert "API tidak mengembalikan response" in result

    def test_chat_none_content_returns_error(self):
        """None content should return error message."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create.return_value = mock_response

        with patch("core.llm_client.get_client", return_value=mock_client):
            result = chat([{"role": "user", "content": "hi"}])
            assert "tidak dapat generate response" in result

    def test_chat_no_api_key_returns_config_error(self):
        """No API key should return configuration error."""
        with patch("core.llm_client.get_client", return_value=None):
            result = chat([{"role": "user", "content": "hi"}])
            assert "API Key belum dikonfigurasi" in result

    def test_chat_retry_on_timeout(self):
        """Should retry on timeout up to MAX_RETRIES."""
        import httpx
        mock_client = MagicMock()
        # First call times out, second succeeds
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Success"
        mock_client.chat.completions.create.side_effect = [
            httpx.TimeoutException("timeout"),
            mock_response,
        ]

        with patch("core.llm_client.get_client", return_value=mock_client):
            with patch("time.sleep"):  # Skip sleep delays
                result = chat([{"role": "user", "content": "hi"}])
                assert result == "Success"
                assert mock_client.chat.completions.create.call_count == 2

    def test_chat_no_retry_on_auth_error(self):
        """Should NOT retry on 401 auth error."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("401 Unauthorized")

        with patch("core.llm_client.get_client", return_value=mock_client):
            result = chat([{"role": "user", "content": "hi"}])
            assert "API Key tidak valid" in result
            assert mock_client.chat.completions.create.call_count == 1


class TestStreaming:
    """Test streaming chat completion."""

    def test_stream_chat_returns_iterator(self):
        """Stream should return an iterator of chunks."""
        mock_client = MagicMock()

        # Create a mock stream that yields chunks
        chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" "))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="World"))]),
        ]
        mock_stream = iter(chunks)
        mock_client.chat.completions.create.return_value = mock_stream

        with patch("core.llm_client.get_client", return_value=mock_client):
            result = chat(messages=[{"role": "user", "content": "hi"}], stream=True)
            # Should be an iterator
            chunks_list = list(result)
            assert chunks_list == ["Hello", " ", "World"]

    def test_stream_chat_skips_empty_deltas(self):
        """Stream should skip chunks with no content delta."""
        mock_client = MagicMock()
        chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
            MagicMock(choices=[MagicMock(delta=None)]),  # Empty
            MagicMock(choices=[]),  # No choices
            MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))]),
        ]
        mock_client.chat.completions.create.return_value = iter(chunks)

        with patch("core.llm_client.get_client", return_value=mock_client):
            result = chat(messages=[{"role": "user", "content": "hi"}], stream=True)
            chunks_list = list(result)
            assert chunks_list == ["Hello", "!"]

    def test_stream_chat_function_alias(self):
        """stream_chat() should be an alias for chat(stream=True)."""
        mock_client = MagicMock()
        chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Test"))]),
        ]
        mock_client.chat.completions.create.return_value = iter(chunks)

        with patch("core.llm_client.get_client", return_value=mock_client):
            result = stream_chat(messages=[{"role": "user", "content": "hi"}])
            assert list(result) == ["Test"]


class TestErrorClassification:
    """Test error classification."""

    def test_network_error_is_retryable(self):
        """Network errors should be retryable."""
        from core.llm_client import _classify_error
        msg, retryable = _classify_error(ConnectionError("Connection refused"))
        assert retryable is True
        assert "Koneksi terputus" in msg

    def test_rate_limit_is_retryable(self):
        """Rate limit (429) should be retryable."""
        from core.llm_client import _classify_error
        msg, retryable = _classify_error(Exception("429 Rate limit exceeded"))
        assert retryable is True
        assert "Server sedang sibuk" in msg

    def test_auth_error_not_retryable(self):
        """Auth error (401) should NOT be retryable."""
        from core.llm_client import _classify_error
        msg, retryable = _classify_error(Exception("401 Unauthorized"))
        assert retryable is False
        assert "API Key tidak valid" in msg

    def test_bad_request_not_retryable(self):
        """400 Bad request should NOT be retryable."""
        from core.llm_client import _classify_error
        msg, retryable = _classify_error(Exception("400 Bad Request"))
        assert retryable is False
        assert "tidak valid" in msg

    def test_server_error_is_retryable(self):
        """500 server errors should be retryable."""
        from core.llm_client import _classify_error
        msg, retryable = _classify_error(Exception("500 Internal Server Error"))
        assert retryable is True


class TestAPIKey:
    """Test API key management."""

    def test_set_api_key_updates_client(self):
        """Setting API key should create new client."""
        with patch("core.llm_client.Groq") as mock_groq:
            set_api_key("test-key-123")
            mock_groq.assert_called_once_with(api_key="test-key-123")
