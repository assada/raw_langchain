from typing import Optional

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    trace_id: str = Field(
        description="Trace ID of the message.",
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    feedback: int = Field(
        description="Feedback score for the run",
        ge=0,
        le=1,
        examples=[0, 1],
    )
    agent_id: Optional[str] = Field(
        None,
        description="The agent ID to run.",
        title="Agent Id",
    )
