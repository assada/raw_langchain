from pydantic import Field

from .base_event import BaseEvent


class ErrorEvent(BaseEvent):
    event: str = "error"
    data: str = Field(
        ...,
        description="The error message, typically a string representation of the error encountered.",
    )
