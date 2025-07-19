import json
from typing import Any

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    event: str = Field(..., description="The type of event")
    data: str = Field(..., description="The data of the event")

    @classmethod
    def from_payload(cls, event: str, payload: dict[str, Any], source: str | None = None) -> "BaseEvent":
        if source:
            payload["source"] = source
        return cls(
            event=event,
            data=json.dumps(payload)
        )
