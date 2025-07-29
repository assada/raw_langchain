from __future__ import annotations

from collections.abc import Sequence
from functools import singledispatch
from typing import Any, overload

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.messages import (
    ChatMessage as LChatMessage,
)

from app.agent.models import (
    AIMessage as CustomAIMessage,
)
from app.agent.models import (
    ChatMessage,
    CustomUIMessage,
    ToolCall,
    ToolResult,
)
from app.agent.models import (
    HumanMessage as CustomHumanMessage,
)

Content = str | Sequence[str | dict[str, Any]]


def _is_tool_use(item: Any) -> bool:
    return isinstance(item, dict) and item.get("type") == "tool_use"


@overload
def strip_tool_calls(content: str) -> str: ...  # type: ignore[overload-overlap]


@overload
def strip_tool_calls(content: Sequence[str | dict]) -> list[str | dict]: ...  # type: ignore[type-arg]


def strip_tool_calls(content: Content) -> Any:
    if isinstance(content, str):
        return content

    return [item for item in content if not _is_tool_use(item)]


@overload
def concat_text(content: str) -> str: ...


@overload
def concat_text(content: Sequence[str | dict]) -> str: ...  # type: ignore[type-arg]


def concat_text(content: Content) -> str:
    if isinstance(content, str):
        return content

    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in content
        if isinstance(item, str) or item.get("type") == "text"
    )


def _attach_trace(msg: ChatMessage, trace_id: str | None) -> ChatMessage:
    if trace_id is not None and hasattr(msg, "trace_id"):
        msg.trace_id = trace_id
    return msg


@singledispatch
def to_chat_message(message: BaseMessage, trace_id: str | None = None) -> ChatMessage:
    raise ValueError(f"Unsupported message type: {type(message).__name__}")


@to_chat_message.register
def _(message: HumanMessage, trace_id: str | None = None) -> ChatMessage:
    return _attach_trace(
        CustomHumanMessage(content=concat_text(message.content)), trace_id
    )


@to_chat_message.register
def _(message: AIMessage, trace_id: str | None = None) -> ChatMessage:
    if message.tool_calls:
        tc = message.tool_calls[0]
        return _attach_trace(
            ToolCall(id=message.id or "", name=tc["name"], args=tc["args"]), trace_id
        )

    return _attach_trace(
        CustomAIMessage(content=concat_text(message.content)), trace_id
    )


@to_chat_message.register
def _(message: ToolMessage, trace_id: str | None = None) -> ChatMessage:
    return _attach_trace(
        ToolResult(
            tool_name=message.name or "unknown_tool",
            content=concat_text(message.content),
            tool_call_id=message.tool_call_id,
        ),
        trace_id,
    )


@to_chat_message.register
def _(message: LChatMessage, trace_id: str | None = None) -> ChatMessage:
    if message.role == "custom":
        return _attach_trace(CustomAIMessage(content=str(message.content[0])), trace_id)

    raise ValueError(f"Unsupported chat message role: {message.role}")


@to_chat_message.register(CustomUIMessage)
def _(message: CustomUIMessage, trace_id: str | None = None) -> ChatMessage:  # type: ignore[misc]
    return _attach_trace(message, trace_id)
