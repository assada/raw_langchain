from pydantic import Field

from .base_event import BaseEvent


class TokenEvent(BaseEvent):
    event: str = "token"
    data: str = Field(
        ...,
        description="The token content, typically a string representation of the token.",
    )
