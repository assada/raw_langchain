from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Content(BaseModel):
    text: str
    type: Literal["text"]
    metadata: dict[str, Any] | None = None


class Content1(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    type: str
    metadata: dict[str, Any] | None = None


class Message(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    role: str = Field(..., description="The role of the message.", title="Role")
    content: str | list[Content | Content1] = Field(
        ..., description="The content of the message.", title="Content"
    )
    id: str | None = Field(None, description="The ID of the message.", title="Id")
    metadata: dict[str, Any] | None = Field(
        None, description="The metadata of the message.", title="Metadata"
    )


class Run(BaseModel):
    input: dict[str, Any] | list[Any] | str | float | bool | None = Field(
        None, description="The input to the agent.", title="Input"
    )
    metadata: dict[str, Any] | None = Field(
        None, description="Metadata to assign to the run.", title="Metadata"
    )
    thread_id: UUID | None = Field(
        None,
        description="The ID of the thread to run.",
        title="Thread Id",
    )
    agent_id: str | None = Field(
        None,
        description="The agent ID to run. If not provided will use the default agent for this service.",
        title="Agent Id",
    )
