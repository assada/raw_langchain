from typing import Literal

from pydantic import BaseModel


class HumanMessage(BaseModel):
    type: Literal["human_message"] = "human_message"
    content: str
