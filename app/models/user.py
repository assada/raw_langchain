from pydantic import BaseModel

class User(BaseModel):
    id: int = 1
    email: str = "test@test.com"