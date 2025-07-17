from typing import Any, Literal

from pydantic import Field

from .chat_message import ChatMessage


class ToolCall(ChatMessage):
    type: Literal["tool_call"] = "tool_call"
    name: str = Field(
        description="Name of the tool to call",
        examples=["weather_tool"],
    )
    args: dict[str, Any] = Field(
        description="Arguments to pass to the tool",
        examples=[{"location": "Kyiv", "date": "2023-10-01"}],
    )
    id: str = Field(
        description="Unique identifier for the tool call",
        examples=["call_sUSKIlBJQ2IkWTNhFShLIB9c"],
    )
