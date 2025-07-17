from typing import Literal

from pydantic import Field

from app.agent.models import ChatMessage


class HumanMessage(ChatMessage):
    type: Literal["human_message"] = "human_message"
    content: str = Field(
        description="Message content",
        examples=["What is the weather like today?"],
    )
