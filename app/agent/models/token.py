from typing import Literal

from pydantic import Field

from .chat_message import ChatMessage


class Token(ChatMessage):
    type: Literal["token"] = "token"
    content: str = Field(
        description="Token content",
        examples=["Hello"],
    )
