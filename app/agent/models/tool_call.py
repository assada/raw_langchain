from typing import Literal

from pydantic import BaseModel


class ToolCall(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    name: str
    args: dict
    id: str
