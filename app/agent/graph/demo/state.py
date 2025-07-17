from __future__ import annotations

from dataclasses import dataclass, field

from langgraph.managed import IsLastStep

from app.agent.graph.base_state import BaseState


@dataclass
class State(BaseState):
    is_last_step: IsLastStep = field(default=False)

    # retrieved_documents: List[Document] = field(default_factory=list)
    # extracted_entities: Dict[str, Any] = field(default_factory=dict)
    # api_connections: Dict[str, Any] = field(default_factory=dict)
