from pydantic import BaseModel

class ToolResult(BaseModel):
    tool_name: str
    content: str
    tool_call_id: str 