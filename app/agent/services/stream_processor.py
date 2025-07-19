import inspect
import json
import logging
from typing import Any, AsyncGenerator
from uuid import UUID

from langchain_core.messages import AIMessage, AIMessageChunk
from langfuse._client.span import LangfuseSpan

from app.agent.models import Token
from app.agent.services.events import TokenEvent, ErrorEvent, EndEvent
from app.agent.services.events.base_event import BaseEvent
from app.agent.utils.utils import remove_tool_calls, langchain_to_chat_message, convert_message_content_to_string

logger = logging.getLogger(__name__)


class StreamProcessor:
    def __init__(self):
        pass

    @staticmethod
    def _create_ai_message(parts: dict) -> AIMessage:
        sig = inspect.signature(AIMessage)
        valid_keys = set(sig.parameters)
        filtered = {k: v for k, v in parts.items() if k in valid_keys}
        return AIMessage(**filtered)

    @staticmethod
    def _process_updates_stream(event: dict[str, Any]) -> list[Any]:
        new_messages = []
        for node, updates in event.items():
            updates = updates or {}
            update_messages = updates.get("messages", [])
            new_messages.extend(update_messages)
        return new_messages

    @staticmethod
    def _process_custom_stream(event: Any) -> list[Any]:
        return [event]

    def _process_messages_for_chat(self, messages: list[Any], run_id: UUID, span: LangfuseSpan = None) -> list[
        BaseEvent]:
        processed_messages = []
        current_message: dict[str, Any] = {}

        for message in messages:
            if isinstance(message, tuple):
                key, value = message
                current_message[key] = value
            else:
                if current_message:
                    processed_messages.append(self._create_ai_message(current_message))
                    current_message = {}
                processed_messages.append(message)

        if current_message:
            processed_messages.append(self._create_ai_message(current_message))

        events = []
        for message in processed_messages:
            try:
                chat_message = langchain_to_chat_message(message)
                chat_message.run_id = str(run_id)

                if (
                        chat_message.type == "human_message"
                        and hasattr(message, 'content') and chat_message.content == message.content
                ):
                    continue
                if span is not None:
                    if chat_message.type == "ai_message":
                        chat_message.trace_id = span.trace_id
                events.append(BaseEvent.from_payload(
                    event=chat_message.type,
                    payload=chat_message.model_dump(),
                    source="stream"
                ))
            except Exception as e:
                logger.error(f"Error parsing message: {e}")
                events.append(ErrorEvent(data=json.dumps({"content": "Unexpected error"})))

        return events

    @staticmethod
    def _process_message_stream(event: tuple, run_id: UUID) -> TokenEvent | None:
        msg, metadata = event

        if "skip_stream" in metadata.get("tags", []):
            return None

        if not isinstance(msg, AIMessageChunk):
            return None

        content = remove_tool_calls(msg.content)
        if not content:
            return None

        token = Token(
            run_id=str(run_id),
            content=convert_message_content_to_string(content),
        )
        return TokenEvent(data=token.model_dump_json())

    async def process_stream(self, stream, run_id: UUID, span: LangfuseSpan = None) -> AsyncGenerator[BaseEvent, None]:
        """TODO: I am not sure about direct passing Span.
        Maybe we can just use Langfuse client directly to get current span.
        """
        async for stream_event in stream:
            if not isinstance(stream_event, tuple):
                continue

            stream_mode, event = stream_event

            if stream_mode == "updates":
                new_messages = self._process_updates_stream(event)
                if new_messages:
                    events = self._process_messages_for_chat(new_messages, run_id, span)
                    for chat_event in events:
                        yield chat_event

            elif stream_mode == "custom":
                new_messages = self._process_custom_stream(event)
                if new_messages:
                    events = self._process_messages_for_chat(new_messages, run_id, span)
                    for chat_event in events:
                        yield chat_event

            elif stream_mode == "messages":
                token_event = self._process_message_stream(event, run_id)
                if token_event:
                    yield token_event

        yield EndEvent(data=json.dumps({"run_id": str(run_id), 'status': 'completed'}))
