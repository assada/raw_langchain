from typing import Literal

from pydantic import Field

from app.agent.models import ChatMessage


class ToolResult(ChatMessage):
    type: Literal["tool_result"] = "tool_result"
    tool_name: str = Field(
        description="Name of the tool that produced this result",
        examples=["weather_tool"],
    )
    content: str = Field(
        description="Tool result content",
        examples=["It's always sunny in Kyiv!"],
    )
    tool_call_id: str = Field(
        description="Tool call id that this result corresponds to",
        examples=["call_sUSKIlBJQ2IkWTNhFShLIB9c"],
    )
