from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import AwareDatetime, BaseModel, Field


class ThreadStatus(Enum):
    idle = "idle"
    busy = "busy"
    interrupted = "interrupted"
    error = "error"


class Thread(BaseModel):
    id: str = Field(
        description="Thread ID.",
        examples=["edd5a53c-da04-4db4-84e0-a9f3592eef45"],
    )
    agent_id: str | None = Field(
        default=None,
        description="The ID of the agent associated with this thread.",
        examples=["agent-12345"],
    )
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="The time the thread was created.",
        examples=["2023-10-01T12:00:00Z"],
    )
    updated_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="The last time the thread was updated.",
        examples=["2023-10-01T12:00:00Z"],
    )
    metadata: dict[str, Any] = Field(
        ..., description="The thread metadata.", title="Metadata"
    )
    status: ThreadStatus | None = Field(
        default=ThreadStatus.idle,
        description="Thread status to filter on.",
        title="Thread Status",
    )
