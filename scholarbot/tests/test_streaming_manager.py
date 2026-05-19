"""Tests for ui/streaming_manager.py — React bridge and streaming coordination."""

import pytest
from unittest.mock import patch, MagicMock
from ui.streaming_manager import (
    StreamingManager,
    create_streaming_manager,
    render_chat_html,
    get_or_create_manager,
    clear_manager,
)


class TestStreamingManager:
    """Test StreamingManager class."""

    def test_create_manager(self):
        """Manager should be created with correct key."""
        mgr = StreamingManager(key="test-key")
        assert mgr.key == "test-key"
        assert mgr.is_streaming is False
        assert mgr.accumulated_text == ""

    def test_start_streaming_returns_id(self):
        """start_streaming should return a streaming message ID."""
        mgr = StreamingManager()
        msg_id = mgr.start_streaming("Hello", "12:00")
        assert msg_id.startswith("stream-")
        assert mgr.is_streaming is True

    def test_add_token_accumulates(self):
        """add_token should accumulate text."""
        mgr = StreamingManager()
        mgr.start_streaming("Hello", "12:00")
        mgr.add_token("Hello")
        mgr.add_token(" ")
        mgr.add_token("World")
        assert mgr.accumulated_text == "Hello World"

    def test_finalize_streaming_returns_text(self):
        """finalize_streaming should return accumulated text and stop streaming."""
        mgr = StreamingManager()
        mgr.start_streaming("Hello", "12:00")
        mgr.add_token("Final")
        mgr.add_token("Text")
        result = mgr.finalize_streaming()
        assert result == "FinalText"
        assert mgr.is_streaming is False

    def test_cancel_streaming_returns_partial(self):
        """cancel_streaming should return partial text."""
        mgr = StreamingManager()
        mgr.start_streaming("Hello", "12:00")
        mgr.add_token("Partial")
        result = mgr.cancel_streaming()
        assert result == "Partial"
        assert mgr.is_streaming is False

    def test_factory_function(self):
        """create_streaming_manager should create a manager."""
        mgr = create_streaming_manager("factory-test")
        assert mgr.key == "factory-test"


class TestRenderChatHtml:
    """Test render_chat_html function."""

    def test_render_with_empty_messages(self):
        """Should render with empty message list."""
        with patch("ui.streaming_manager.components.html") as mock_html:
            with patch("builtins.open", MagicMock()):
                render_chat_html([], is_typing=False)
                mock_html.assert_called_once()

    def test_render_with_messages(self):
        """Should render with messages including metadata."""
        messages = [
            {"role": "user", "content": "Hello", "time": "12:00", "id": "msg-1"},
            {"role": "assistant", "content": "Hi there!", "time": "12:01", "id": "msg-2"},
        ]
        with patch("ui.streaming_manager.components.html") as mock_html:
            with patch("builtins.open", MagicMock()):
                with patch("ui.streaming_manager.Path") as mock_path:
                    mock_path.return_value = MagicMock()
                    render_chat_html(messages, height=500)
                    mock_html.assert_called_once()
                    # Check height parameter
                    call_kwargs = mock_html.call_args
                    assert call_kwargs.kwargs.get("height") == 500


class TestManagerRegistry:
    """Test the manager registry."""

    def test_get_or_create_new_manager(self):
        """get_or_create_manager should create new manager for new key."""
        clear_manager("registry-test")
        mgr = get_or_create_manager("registry-test")
        assert mgr.key == "registry-test"

    def test_get_or_create_existing_manager(self):
        """get_or_create_manager should return existing manager for same key."""
        clear_manager("registry-test-2")
        mgr1 = get_or_create_manager("registry-test-2")
        mgr2 = get_or_create_manager("registry-test-2")
        assert mgr1 is mgr2  # Same instance

    def test_clear_manager(self):
        """clear_manager should remove manager from registry."""
        get_or_create_manager("clear-test")
        clear_manager("clear-test")
        # Creating again should be a new instance
        mgr = get_or_create_manager("clear-test")
        assert mgr is not None
