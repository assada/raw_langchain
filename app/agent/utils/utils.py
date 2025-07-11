"""Utility & helper functions for the agent."""

import logging

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)

from langchain_core.messages import (
    ChatMessage as LangchainChatMessage,
)

from app.agent.models import ToolCall, ToolResult, AIMessage as CustomAIMessage, HumanMessage as CustomHumanMessage

logger = logging.getLogger(__name__)


def get_message_text(msg: BaseMessage) -> str:
    """Get the text content of a message."""
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()


def load_chat_model(fully_specified_name: str) -> BaseChatModel:
    """Load a chat model from a fully specified name.

    Args:
        fully_specified_name (str): String in the format 'provider/model'.
    """
    logger.debug(f"Loading chat model: {fully_specified_name}")
    provider, model = fully_specified_name.split("/", maxsplit=1)
    logger.debug(f"Provider: {provider}, Model: {model}")
    return init_chat_model(model, model_provider=provider)

def remove_tool_calls(content: str | list[str | dict]) -> str | list[str | dict]:
    """Remove tool calls from content."""
    if isinstance(content, str):
        return content
    return [
        content_item
        for content_item in content
        if isinstance(content_item, str) or content_item["type"] != "tool_use"
    ]

def convert_message_content_to_string(content: str | list[str | dict]) -> str:
    if isinstance(content, str):
        return content
    text: list[str] = []
    for content_item in content:
        if isinstance(content_item, str):
            text.append(content_item)
            continue
        if content_item["type"] == "text":
            text.append(content_item["text"])
    return "".join(text)

def langchain_to_chat_message(message: BaseMessage) -> CustomAIMessage | CustomHumanMessage | ToolMessage:
    """Create a ChatMessage from a LangChain message."""
    match message:
        case HumanMessage():
            return CustomHumanMessage(content=convert_message_content_to_string(message.content))
        case AIMessage():
            if message.tool_calls:
                logger.debug(f"Tool calls: {message.tool_calls[0]}")
                return ToolCall(
                    id=message.id,
                    name=message.tool_calls[0]["name"],
                    args=message.tool_calls[0]["args"],
                )
            return CustomAIMessage(content=convert_message_content_to_string(message.content))
        case ToolMessage():
            return ToolResult(
                tool_name=message.name,
                content=convert_message_content_to_string(message.content),
                tool_call_id=message.tool_call_id,
            )
        case LangchainChatMessage():
            if message.role == "custom":
                return CustomAIMessage(content=message.content[0])
            else:
                raise ValueError(f"Unsupported chat message role: {message.role}")
        case _:
            raise ValueError(f"Unsupported message type: {message.__class__.__name__}")
