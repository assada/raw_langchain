import logging
from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langfuse import Langfuse
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from app.agent.graph.base_state import BaseState
from app.agent.graph.demo.state import State
from app.agent.graph.demo.tools.tools import TOOLS
from app.agent.graph.graph import Graph
from app.agent.utils.utils import load_chat_model

logger = logging.getLogger(__name__)


class DemoGraph(Graph):
    def __init__(self, checkpointer: BaseCheckpointSaver, langfuse: Langfuse):
        self._checkpointer = checkpointer
        self._langfuse = langfuse
        self.graph_name = "demo_graph"

    def build_graph(self) -> CompiledStateGraph:
        """Build the StateGraph for the agent."""

        async def call_model(state: State, config: RunnableConfig) -> Dict[str, List[AIMessage]]:
            langfuse_prompt = self._langfuse.get_prompt(
                self.graph_name,
                label="production",
                fallback="You are a helpful assistant."
            )

            model = load_chat_model(
                langfuse_prompt.config.get("model", "openai/4o-mini"),
                temperature=langfuse_prompt.config.get("temperature", 1)
            ).bind_tools(TOOLS)

            prompt = (
                ChatPromptTemplate.from_messages(
                    [
                        ("system", langfuse_prompt.get_langchain_prompt()),
                        MessagesPlaceholder("history"),
                    ]
                )
                .partial(system_time=datetime.now(tz=UTC).isoformat())
            )
            prompt.metadata = {"langfuse_prompt": langfuse_prompt}

            chain = prompt | model

            response = cast(
                AIMessage,
                await chain.ainvoke(
                    {"history": state.messages},
                    config=config,
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

        builder = StateGraph(State, input=BaseState)

        builder.add_node("call_model", call_model)
        builder.add_node("tools", ToolNode(TOOLS))

        builder.add_edge(START, "call_model")
        builder.add_conditional_edges("call_model", route_model_output)
        builder.add_edge("tools", "call_model")

        return builder.compile(checkpointer=self._checkpointer, name=self.graph_name)
