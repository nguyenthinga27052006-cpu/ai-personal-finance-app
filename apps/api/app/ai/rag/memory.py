from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from app.ai.errors import AuthorizationError
from app.ai.guardrails import validate_untrusted_input


@dataclass(frozen=True)
class RAGMessage:
    message_id: str
    conversation_id: str
    user_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RAGMemoryStore:
    """Bounded conversation memory store keeping up to 10 recent conversation turns per session/user."""

    def __init__(self, max_turns: int = 10, max_tokens: int = 2500) -> None:
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self._conversations: dict[str, list[RAGMessage]] = {}
        self._owners: dict[str, str] = {}

    def add_message(
        self,
        user_id: str,
        content: str,
        role: Literal["user", "assistant"] = "user",
        conversation_id: str | None = None,
    ) -> RAGMessage:
        validate_untrusted_input(content)
        conv_id = conversation_id or f"conv_{user_id}"
        owner = self._owners.setdefault(conv_id, user_id)
        if owner != user_id:
            raise AuthorizationError("Conversation does not belong to the authenticated user")

        msg = RAGMessage(
            message_id=str(uuid4()),
            conversation_id=conv_id,
            user_id=user_id,
            role=role,
            content=content.strip(),
        )
        entries = self._conversations.setdefault(conv_id, [])
        entries.append(msg)

        # Retain maximum 10 recent turns (20 messages user+assistant)
        max_messages = self.max_turns * 2
        if len(entries) > max_messages:
            del entries[:-max_messages]

        return msg

    def get_history(self, user_id: str, conversation_id: str | None = None) -> list[RAGMessage]:
        conv_id = conversation_id or f"conv_{user_id}"
        if self._owners.get(conv_id) not in (None, user_id):
            raise AuthorizationError("Conversation does not belong to the authenticated user")
        return list(self._conversations.get(conv_id, []))

    def get_formatted_context(self, user_id: str, conversation_id: str | None = None) -> str:
        history = self.get_history(user_id, conversation_id)
        if not history:
            return "Chưa có ngữ cảnh hội thoại trước đó."

        formatted = []
        for msg in history:
            role_label = "Người dùng" if msg.role == "user" else "Trợ lý AI"
            formatted.append(f"{role_label}: {msg.content}")

        return "\n".join(formatted)


_global_memory: RAGMemoryStore | None = None


def get_memory_store() -> RAGMemoryStore:
    global _global_memory
    if _global_memory is None:
        _global_memory = RAGMemoryStore(max_turns=10)
    return _global_memory
