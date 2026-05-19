"""Tests for ui/react_bridge.py — Streamlit-React bridge utilities."""

import pytest
import json
from unittest.mock import patch, MagicMock
from ui.react_bridge import render_custom_chat, render_welcome_screen


class TestRenderCustomChat:
    """Test render_custom_chat function."""

    def test_renders_with_empty_messages(self):
        """Should render component with empty message list."""
        mock_html_content = "<!DOCTYPE html><html><body><script>window.STREAMLIT_MESSAGES || []; window.STREAMLIT_IS_TYPING || false; window.STREAMLIT_STREAMING_ID || null;</script></body></html>"
        with patch("ui.react_bridge.components.html") as mock_html:
            with patch("builtins.open", MagicMock()) as mock_file:
                mock_file.return_value.read.return_value = mock_html_content
                render_custom_chat([], is_typing=False)
                mock_html.assert_called_once()

    def test_injects_messages_data(self):
        """Should inject messages into window globals."""
        messages = [
            {"role": "user", "content": "Hello", "time": "12:00"},
            {"role": "assistant", "content": "Hi there!", "time": "12:01"},
        ]

        mock_html_content = (
            "<!DOCTYPE html><html><body>"
            "<script>window.STREAMLIT_MESSAGES || [];"
            "window.STREAMLIT_IS_TYPING || false;"
            "window.STREAMLIT_STREAMING_ID || null;"
            "</script></body></html>"
        )
        with patch("ui.react_bridge.components.html") as mock_html:
            with patch("builtins.open", MagicMock()) as mock_file:
                mock_file.return_value.read.return_value = mock_html_content
                render_custom_chat(messages, is_typing=False)

                call_kwargs = mock_html.call_args
                rendered_html = call_kwargs[0][0]

                # Check messages were injected
                assert "STREAMLIT_MESSAGES" in rendered_html
                assert "Hello" in rendered_html
                assert "Hi there!" in rendered_html

    def test_typing_indicator_flag(self):
        """Should inject is_typing flag."""
        mock_html_content = (
            "<!DOCTYPE html><html><body>"
            "<script>window.STREAMLIT_MESSAGES || [];"
            "window.STREAMLIT_IS_TYPING || false;"
            "window.STREAMLIT_STREAMING_ID || null;"
            "</script></body></html>"
        )
        with patch("ui.react_bridge.components.html") as mock_html:
            with patch("builtins.open", MagicMock()) as mock_file:
                mock_file.return_value.read.return_value = mock_html_content
                render_custom_chat([], is_typing=True)

                call_kwargs = mock_html.call_args
                rendered_html = call_kwargs[0][0]
                assert '"isTyping":true' in rendered_html or "true" in rendered_html

    def test_streaming_message_id_injection(self):
        """Should inject streaming message ID."""
        mock_html_content = (
            "<!DOCTYPE html><html><body>"
            "<script>window.STREAMLIT_MESSAGES || [];"
            "window.STREAMLIT_IS_TYPING || false;"
            "window.STREAMLIT_STREAMING_ID || null;"
            "</script></body></html>"
        )
        with patch("ui.react_bridge.components.html") as mock_html:
            with patch("builtins.open", MagicMock()) as mock_file:
                mock_file.return_value.read.return_value = mock_html_content
                render_custom_chat([], is_typing=False, streaming_message_id="test-stream-123")

                call_kwargs = mock_html.call_args
                rendered_html = call_kwargs[0][0]
                assert "test-stream-123" in rendered_html


class TestRenderWelcomeScreen:
    """Test render_welcome_screen function."""

    def test_renders_without_user_name(self):
        """Should render with default greeting when no name."""
        with patch("ui.react_bridge.components.html") as mock_html:
            render_welcome_screen(user_name="")
            mock_html.assert_called_once()

    def test_renders_with_user_name(self):
        """Should render personalized greeting with name."""
        with patch("ui.react_bridge.components.html") as mock_html:
            render_welcome_screen(user_name="Andi")
            mock_html.assert_called_once()
            # Check that greeting is in HTML
            call_args_str = str(mock_html.call_args)
            assert "Andi" in call_args_str

    def test_default_suggestion_chips(self):
        """Should have default suggestion chips."""
        with patch("ui.react_bridge.components.html") as mock_html:
            render_welcome_screen()
            call_args_str = str(mock_html.call_args)
            # Should include default chips
            assert "Pythagoras" in call_args_str or "Teorema" in call_args_str

    def test_custom_suggestion_chips(self):
        """Should use custom suggestion chips when provided."""
        custom_chips = [
            ("Custom Topic 1", "Ask about custom topic 1"),
            ("Custom Topic 2", "Ask about custom topic 2"),
        ]
        with patch("ui.react_bridge.components.html") as mock_html:
            render_welcome_screen(suggestion_chips=custom_chips)
            call_args_str = str(mock_html.call_args)
            assert "Custom Topic 1" in call_args_str
            assert "Custom Topic 2" in call_args_str
