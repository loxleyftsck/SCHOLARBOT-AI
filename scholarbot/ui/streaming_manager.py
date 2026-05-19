"""Streamlit-React Streaming Manager.

Handles streaming chat rendering in Streamlit using React components.
Manages the streaming state, markdown rendering, and auto-scroll coordination.

Architecture:
  1. app.py calls StreamingManager.start_streaming() when user sends a message
  2. Manager creates an st.empty() container for the bot's streaming response
  3. Each token is accumulated and rendered as markdown in real-time
  4. When complete, the final message is added to session_state.messages
  5. React component receives data via window globals and renders with animations

This bridges Streamlit's Python world with React's JavaScript world.
"""

import time
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from typing import Optional, Callable, Iterator, List, Dict
import json


class StreamingManager:
    """Manages streaming chat messages in Streamlit with React component rendering.

    Usage:
        manager = StreamingManager(key="chat_main")

        # Start streaming
        manager.start_streaming()

        # Accumulate tokens (called by app.py's streaming loop)
        for token in stream_tokens():
            manager.add_token(token)
            time.sleep(0.01)  # Simulate real-time

        # Finalize
        final_text = manager.finalize_streaming()
        # final_text is now ready to be added to messages
    """

    def __init__(self, key: str = "default"):
        """Initialize the streaming manager.

        Args:
            key: Unique identifier for this chat instance (used in React component)
        """
        self.key = key
        self._container: Optional[st.delta_generator.DeltaGenerator] = None
        self._accumulated_text: str = ""
        self._is_streaming: bool = False
        self._streaming_message_id: Optional[str] = None
        self._html_placeholder: Optional[object] = None

    @property
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self._is_streaming

    @property
    def accumulated_text(self) -> str:
        """Get the accumulated streaming text so far."""
        return self._accumulated_text

    def _get_html_path(self) -> Path:
        """Get the path to the chat component HTML file."""
        return Path(__file__).parent / "chat_component.html"

    def _build_react_html(self,
                          messages: List[Dict],
                          is_typing: bool = False,
                          streaming_message_id: Optional[str] = None,
                          is_regenerating: bool = False) -> str:
        """Build the React component HTML with injected data.

        Args:
            messages: List of message dicts with role, content, time, id
            is_typing: Show typing indicator
            streaming_message_id: ID of message being streamed
            is_regenerating: Show regenerate loading state

        Returns:
            Complete HTML string ready to render
        """
        template_path = self._get_html_path()
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Prepare messages for JSON injection
        prepared_messages = []
        for msg in messages:
            prepared_messages.append({
                "id": msg.get("id", None),
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
                "time": msg.get("time", ""),
            })

        # Inject data via window globals
        data = {
            "messages": prepared_messages,
            "isTyping": is_typing,
            "streamingMessageId": streaming_message_id,
            "isRegenerating": is_regenerating,
            "key": self.key,
        }

        html = html.replace(
            "window.STREAMLIT_MESSAGES || []",
            f"window.STREAMLIT_MESSAGES = {json.dumps(prepared_messages, ensure_ascii=False)}; window.STREAMLIT_MESSAGES"
        )
        html = html.replace(
            "window.STREAMLIT_IS_TYPING || false",
            f"window.STREAMLIT_IS_TYPING = {json.dumps(is_typing)}; window.STREAMLIT_IS_TYPING"
        )
        html = html.replace(
            "window.STREAMLIT_STREAMING_ID || null",
            f"window.STREAMLIT_STREAMING_ID = {json.dumps(streaming_message_id)}; window.STREAMLIT_STREAMING_ID"
        )
        html = html.replace(
            "window.STREAMLIT_KEY || 'chat-default'",
            f"window.STREAMLIT_KEY = {json.dumps(self.key)}; window.STREAMLIT_KEY"
        )
        html = html.replace(
            "window.STREAMLIT_REGENERATING || false",
            f"window.STREAMLIT_REGENERATING = {json.dumps(is_regenerating)}; window.STREAMLIT_REGENERATING"
        )

        return html

    def render_react_component(self,
                                messages: List[Dict],
                                is_typing: bool = False,
                                streaming_message_id: Optional[str] = None,
                                is_regenerating: bool = False,
                                height: int = 600) -> None:
        """Render the React chat component with current state.

        Args:
            messages: All messages to display
            is_typing: Show typing indicator
            streaming_message_id: ID of message being streamed
            is_regenerating: Show regenerate loading state
            height: Component height in pixels
        """
        html = self._build_react_html(
            messages=messages,
            is_typing=is_typing,
            streaming_message_id=streaming_message_id,
            is_regenerating=is_regenerating,
        )

        components.html(
            html,
            height=height,
            scrolling=True,
        )

    def render_streaming_update(self,
                                 messages: List[Dict],
                                 streaming_text: str,
                                 streaming_message_id: str) -> None:
        """Render a streaming update - optimized for fast token updates.

        Uses minimal re-renders to keep up with rapid token streaming.

        Args:
            messages: All messages including the one being streamed
            streaming_text: Current accumulated text of the streaming message
            streaming_message_id: ID of the streaming message
        """
        # Create a copy of messages with the streaming message's content updated
        updated_messages = []
        for msg in messages:
            if msg.get("id") == streaming_message_id:
                updated_messages.append({
                    **msg,
                    "content": streaming_text,
                })
            else:
                updated_messages.append(msg)

        # Render with React component
        self.render_react_component(
            messages=updated_messages,
            is_typing=False,
            streaming_message_id=streaming_message_id,
        )

    def render_typing_indicator(self, messages: List[Dict]) -> None:
        """Render with typing indicator shown."""
        self.render_react_component(
            messages=messages,
            is_typing=True,
        )

    def start_streaming(self, user_message: str, time_str: str) -> str:
        """Start a new streaming message.

        Creates the streaming message entry and returns its ID.

        Args:
            user_message: The user's message text
            time_str: Current timestamp string

        Returns:
            The streaming message ID
        """
        import uuid
        self._is_streaming = True
        self._accumulated_text = ""
        self._streaming_message_id = f"stream-{uuid.uuid4().hex[:12]}"

        return self._streaming_message_id

    def add_token(self, token: str) -> None:
        """Add a token to the accumulated streaming text.

        Args:
            token: A text chunk to append
        """
        self._accumulated_text += token

    def finalize_streaming(self) -> str:
        """Finalize the streaming message and return the final text.

        Returns:
            The final complete text
        """
        self._is_streaming = False
        return self._accumulated_text

    def cancel_streaming(self) -> str:
        """Cancel the current streaming and return partial text.

        Returns:
            The partial text accumulated so far
        """
        self._is_streaming = False
        return self._accumulated_text


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_streaming_manager(key: str = "default") -> StreamingManager:
    """Factory function to create a StreamingManager."""
    return StreamingManager(key=key)


def render_chat_html(messages: List[Dict],
                      is_typing: bool = False,
                      streaming_message_id: Optional[str] = None,
                      height: int = 600,
                      key: str = "default") -> None:
    """Render the React chat component with given messages.

    Args:
        messages: List of message dicts
        is_typing: Show typing indicator
        streaming_message_id: ID of streaming message
        height: Component height
        key: Component key
    """
    manager = StreamingManager(key=key)
    manager.render_react_component(
        messages=messages,
        is_typing=is_typing,
        streaming_message_id=streaming_message_id,
        height=height,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# STREAMLIT COMPONENT BRIDGE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

# Global registry for Streamlit-JS communication
_component_registry: Dict[str, StreamingManager] = {}


def get_or_create_manager(key: str = "default") -> StreamingManager:
    """Get or create a StreamingManager for the given key."""
    if key not in _component_registry:
        _component_registry[key] = StreamingManager(key=key)
    return _component_registry[key]


def clear_manager(key: str = "default") -> None:
    """Clear a StreamingManager from the registry."""
    if key in _component_registry:
        del _component_registry[key]
