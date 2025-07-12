from typing import Any

from pydantic import BaseModel


class ChatHistory(BaseModel):
    messages: list[Any]
