import logging
from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langgraph.graph import START, END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from app.agent.graph.graph import Graph
from app.agent.state import InputState, State
from app.agent.tools.tools import TOOLS
from app.agent.utils.utils import load_chat_model
from app.bootstrap.config import AppConfig

logger = logging.getLogger(__name__)


class DemoGraph(Graph):
    def __init__(self, config: AppConfig, checkpointer):
        self.config = config
        self.checkpointer = checkpointer

    def build_graph(self) -> CompiledStateGraph:
        """Build the StateGraph for the agent."""

        async def call_model(state: State) -> Dict[str, List[AIMessage]]:
            """Call the LLM powering our agent."""
            model = load_chat_model(self.config.agent_model).bind_tools(TOOLS)

            system_message = self.config.agent_prompt.format(
                system_time=datetime.now(tz=UTC).isoformat()
            )

            response = cast(
                AIMessage,
                await model.ainvoke(
                    [{"role": "system", "content": system_message}, *state.messages]
                ),
            )

            if state.is_last_step and response.tool_calls:
                return {
                    "messages": [
                        AIMessage(
                            id=response.id,
                            content="Sorry, I could not find an answer to your question in the specified number of steps.",
                        )
                    ]
                }

            return {"messages": [response]}

        def route_model_output(state: State) -> Literal[END, "tools"]:
            """Determine the next node based on the model's output."""
            last_message = state.messages[-1]
            if not isinstance(last_message, AIMessage):
                raise ValueError(
                    f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
                )
            if not last_message.tool_calls:
                return END
            return "tools"

        builder = StateGraph(State, input=InputState)

        builder.add_node("call_model", call_model)
        builder.add_node("tools", ToolNode(TOOLS))

        builder.add_edge(START, "call_model")
        builder.add_conditional_edges("call_model", route_model_output)
        builder.add_edge("tools", "call_model")

        return builder.compile(checkpointer=self.checkpointer)
