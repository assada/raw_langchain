from pydantic import Field

from .base_event import BaseEvent


class EndEvent(BaseEvent):
    event: str = "stream_end"
    data: str = Field(...,description="The end of the stream event, typically a string indicating the end of the stream.")
