from typing import Literal
from pydantic import BaseModel

class AIMessage(BaseModel):
    type: Literal["ai_message"] = "ai_message"
    content: str 