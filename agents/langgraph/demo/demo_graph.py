import logging
from typing import Any, Literal

from langchain_core.messages import AIMessage

from app.agent.frameworks.langgraph_framework import Graph
from app.agent.frameworks.langgraph_framework.base_state import BaseState, State
from app.agent.prompt import PromptProvider
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from .tools import TOOLS

logger = logging.getLogger(__name__)


class DemoGraph(Graph):
    def __init__(
            self, checkpointer: BaseCheckpointSaver[Any], prompt_provider: PromptProvider, custom_config: dict[str, Any] | None = None
    ):
        super().__init__(checkpointer, prompt_provider)

    @property
    def graph_name(self) -> str:
        return "demo_agent"

    def get_tools(self) -> list[Any]:
        return TOOLS

    def build_graph(self) -> CompiledStateGraph[State, BaseState, Any]:
        def route_model_output(state: State) -> Literal["__end__", "tools"]:
            last_message = state.messages[-1]
            if not isinstance(last_message, AIMessage):
                raise ValueError(
                    f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
                )
            if not last_message.tool_calls:
                return "__end__"
            return "tools"

        builder: StateGraph[State, BaseState, Any] = StateGraph(
            state_schema=State, input_schema=BaseState
        )

        builder.add_node("call_model", self.call_model)
        builder.add_node("tools", ToolNode(TOOLS))

        builder.add_edge(START, "call_model")
        builder.add_conditional_edges("call_model", route_model_output)
        builder.add_edge("tools", "call_model")

        return builder.compile(checkpointer=self._checkpointer, name=self.graph_name)
