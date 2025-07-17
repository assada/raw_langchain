from typing import Literal

from pydantic import Field

from .chat_message import ChatMessage


class HumanMessage(ChatMessage):
    type: Literal["human_message"] = "human_message"
    content: str = Field(
        description="Message content",
        examples=["What is the weather like today?"],
    )
