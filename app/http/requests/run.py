from typing import Optional, Union, Dict, Any, List, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class Content(BaseModel):
    text: str
    type: Literal["text"]
    metadata: Optional[Dict[str, Any]] = None


class Content1(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    type: str
    metadata: Optional[Dict[str, Any]] = None


class Message(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    role: str = Field(..., description="The role of the message.", title="Role")
    content: Union[str, List[Union[Content, Content1]]] = Field(
        ..., description="The content of the message.", title="Content"
    )
    id: Optional[str] = Field(None, description="The ID of the message.", title="Id")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="The metadata of the message.", title="Metadata"
    )


class Run(BaseModel):
    input: Union[Dict[str, Any], List, str, float, bool] = Field(
        None, description="The input to the agent.", title="Input"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Metadata to assign to the run.", title="Metadata"
    )
    thread_id: UUID = Field(
        None,
        description="The ID of the thread to run.",
        title="Thread Id",
    )
    agent_id: Optional[str] = Field(
        None,
        description="The agent ID to run. If not provided will use the default agent for this service.",
        title="Agent Id",
    )
