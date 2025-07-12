from pydantic import BaseModel, Field


class User(BaseModel):
    id: str = Field(
        description="User Unique ID.",
        examples=["1437ade37359488e95c0727a1cdf1786d24edce3"]
    )
    email: str = "test@test.com"
