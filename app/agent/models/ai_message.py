from pydantic import BaseModel

class AIMessage(BaseModel):
    content: str 