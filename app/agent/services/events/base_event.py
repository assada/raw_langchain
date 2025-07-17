from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    event: str = Field(..., description="The type of event")
    data: str = Field(..., description="The data of the event")
