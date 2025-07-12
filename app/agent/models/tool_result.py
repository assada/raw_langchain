from typing import Literal

from pydantic import BaseModel


class ToolResult(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    tool_name: str
    content: str
    tool_call_id: str
