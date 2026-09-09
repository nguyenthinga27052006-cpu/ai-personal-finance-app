from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from app.ai.errors import AuthorizationError
from app.ai.guardrails import validate_untrusted_input


@dataclass(frozen=True)
class ConversationMessage:
    conversation_id: str
    user_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationStore:
    _messages: dict[str, list[ConversationMessage]]

    def __init__(self, max_messages: int = 8, max_tokens: int = 1800) -> None:
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self._messages = {}
        self._owners: dict[str, str] = {}

    def create(
        self,
        user_id: str,
        content: str,
        *,
        role: str = "user",
        conversation_id: str | None = None,
    ) -> ConversationMessage:
        validate_untrusted_input(content)
        conversation_id = conversation_id or str(uuid4())
        owner = self._owners.setdefault(conversation_id, user_id)
        if owner != user_id:
            raise AuthorizationError("Conversation does not belong to the authenticated user")
        message = ConversationMessage(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content.strip(),
        )
        entries = self._messages.setdefault(conversation_id, [])
        entries.append(message)
        if len(entries) > self.max_messages:
            del entries[:-self.max_messages]
        return message

    def list(
        self,
        user_id: str,
        *,
        conversation_id: str | None = None,
        limit: int | None = None,
    ) -> list[ConversationMessage]:
        if conversation_id is not None and self._owners.get(conversation_id) not in (None, user_id):
            raise AuthorizationError("Conversation does not belong to the authenticated user")
        conversation_ids = (
            [conversation_id]
            if conversation_id is not None
            else [item for item, owner in self._owners.items() if owner == user_id]
        )
        messages = [
            message
            for item in conversation_ids
            for message in self._messages.get(item, [])
            if message.user_id == user_id
        ]
        messages.sort(key=lambda item: item.created_at)
        if limit is not None:
            return messages[-limit:]
        return messages

    def bounded_context(self, user_id: str) -> list[ConversationMessage]:
        messages = self.list(user_id, limit=self.max_messages)
        tokens = 0
        selected: list[ConversationMessage] = []
        for message in reversed(messages):
            tokens += len(message.content.split())
            if tokens > self.max_tokens:
                break
            selected.insert(0, message)
        return selected

    def summarize(self, user_id: str) -> str:
        messages = self.bounded_context(user_id)
        if not messages:
            return "No recent conversation context."
        return " | ".join(f"{m.role}:{m.content}" for m in messages)
