from typing import Literal

from pydantic import Field

from app.agent.models.ChatMessage import ChatMessage


class AIMessage(ChatMessage):
    type: Literal["ai_message"] = "ai_message"
    content: str = Field(
        description="Message content",
        examples=["In the morning, the sun rises in the east and sets in the west."],
    )
