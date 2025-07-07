from pydantic import BaseModel

class ToolResultModel(BaseModel):
    tool_name: str
    content: str
    tool_call_id: str