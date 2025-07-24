import logging
from typing import List, Literal

from langchain_core.messages import AIMessage
from langfuse import Langfuse
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from app.agent.graph import Graph
from app.agent.graph.base_state import BaseState
from app.agent.graph.demo.state import State
from app.agent.graph.demo.tools.tools import TOOLS

logger = logging.getLogger(__name__)


class DemoGraph(Graph[State]):
    def __init__(self, checkpointer: BaseCheckpointSaver, langfuse: Langfuse):
        super().__init__(checkpointer, langfuse)

    @property
    def graph_name(self) -> str:
        return "demo_graph"

    def get_tools(self) -> List:
        return TOOLS

    def build_graph(self) -> CompiledStateGraph:
        def route_model_output(state: State) -> Literal[END, "tools"]:
            last_message = state.messages[-1]
            if not isinstance(last_message, AIMessage):
                raise ValueError(
                    f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
                )
            if not last_message.tool_calls:
                return END
            return "tools"

        builder = StateGraph(State, input=BaseState)

        builder.add_node("call_model", self.call_model)
        builder.add_node("tools", ToolNode(TOOLS))

        builder.add_edge(START, "call_model")
        builder.add_conditional_edges("call_model", route_model_output)
        builder.add_edge("tools", "call_model")

        return builder.compile(checkpointer=self._checkpointer, name=self.graph_name)
