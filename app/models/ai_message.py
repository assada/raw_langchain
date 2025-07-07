from pydantic import BaseModel

class AIMessageModel(BaseModel):
    content: str