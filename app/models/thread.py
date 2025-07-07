from pydantic import BaseModel

class Thread(BaseModel):
    id: int
    user_id: int