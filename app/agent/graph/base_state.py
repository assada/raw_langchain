from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated


@dataclass
class BaseState:
    messages: Annotated[Sequence[AnyMessage], add_messages] = field(
        default_factory=list
    )
