"""Core assistant functions for command processing and speech output."""
from __future__ import annotations

from typing import Callable, Any


def speak(assistant: Any, text: str, callback: Callable[[str], None] | None = None) -> None:
    """Speak ``text`` using the assistant's TTS engine.

    Parameters
    ----------
    assistant: Any
        Object containing TTS engine and configuration.
    text: str
        Text to be spoken.
    callback: Callable[[str], None] | None, optional
        Function invoked with ``text`` after speaking. This allows UIs to
        display the spoken text.
    """
    print(f"Nexus: {text}")
    if not getattr(assistant, "silence", False):
        assistant.tts.say(text)
        assistant.tts.runAndWait()
    cb = callback or getattr(assistant, "speak_callback", None)
    if cb:
        cb(text)


def process_text(assistant: Any, text: str) -> None:
    """Process incoming ``text`` against registered commands.

    If no command matches, the text is forwarded to the fallback chat
    mechanism implemented by ``assistant._chatgpt``.
    """
    for trigger, (action, mode) in assistant.commands.items():
        if mode == "startswith" and text.startswith(trigger):
            action(text)
            return
        if mode == "in" and trigger in text:
            action(text)
            return
    assistant._chatgpt(text)
