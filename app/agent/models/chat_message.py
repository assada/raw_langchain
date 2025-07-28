from typing import Literal

from pydantic import BaseModel, Field

MessageType = Literal[
    "unknown",
    "tool_result",
    "tool_call",
    "token",
    "human_message",
    "ui",
    "ai_message",
]

class ChatMessage(BaseModel):
    type: MessageType = "unknown"
    run_id: str | None = Field(
        description="Run ID of the message.",
        default=None,
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    trace_id: str | None = Field(
        description="Trace ID of the message.",
        default=None,
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
