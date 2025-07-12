from pydantic import BaseModel, Field


class Thread(BaseModel):
    id: str = Field(
        description="Thread ID.",
        examples=["edd5a53c-da04-4db4-84e0-a9f3592eef45"],
    )
