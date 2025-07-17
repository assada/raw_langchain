from typing import Literal

from pydantic import Field

from app.agent.models import ChatMessage


class Token(ChatMessage):
    type: Literal["token"] = "token"
    content: str = Field(
        description="Token content",
        examples=["Hello"],
    )
