from pydantic import BaseModel

class ToolCall(BaseModel):
    name: str
    args: dict
    id: str 