from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.messages import (
    ChatMessage as LangchainChatMessage,
)

from app.agent.models import ToolCall, ToolResult, AIMessage as CustomAIMessage, HumanMessage as CustomHumanMessage, \
    CustomUIMessage, ModelConfig
from app.agent.models import ChatMessage


def load_chat_model(model_config: ModelConfig) -> BaseChatModel:
    provider, model = model_config.model.split("/", maxsplit=1)
    return init_chat_model(model, model_provider=provider)


def remove_tool_calls(content: str | list[str | dict]) -> str | list[str | dict]:
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


def langchain_to_chat_message(message: BaseMessage) -> ChatMessage:
    match message:
        case HumanMessage():
            return CustomHumanMessage(content=convert_message_content_to_string(message.content))
        case AIMessage():
            if message.tool_calls:
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
        case CustomUIMessage():
            return message
        case _:
            raise ValueError(f"Unsupported message type: {message.__class__.__name__}")
