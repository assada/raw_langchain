from app.agent.graph.graph import Graph
from app.agent.tools.tools import TOOLS
from app.agent.state import State, InputState
from app.agent.utils.utils import load_chat_model

from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver


from datetime import UTC, datetime
import logging

from app.bootstrap.config import AppConfig


logger = logging.getLogger(__name__)

class DemoGraph(Graph):

    def __init__(self, config: AppConfig):
        self.config = config

    def build_graph(self):
        """Build the StateGraph for the agent."""

        logger.info("Building the graph for the agent.")
        
        async def call_model(state: State) -> Dict[str, List[AIMessage]]:
            """Call the LLM powering our agent."""
            logger.debug("Calling the model for the agent.")
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

            logger.debug(f"Response from the model: {response}")
            
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
            
        def route_model_output(state: State) -> Literal["__end__", "tools"]:
            """Determine the next node based on the model's output."""
            last_message = state.messages[-1]
            if not isinstance(last_message, AIMessage):
                raise ValueError(
                    f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
                )
            if not last_message.tool_calls:
                return "__end__"
            return "tools"
        
        builder = StateGraph(State, input=InputState)
        
        builder.add_node("call_model", call_model)
        builder.add_node("tools", ToolNode(TOOLS))
        
        builder.add_edge("__start__", "call_model")
        builder.add_conditional_edges("call_model", route_model_output)
        builder.add_edge("tools", "call_model")
        
        checkpointer = InMemorySaver()
        return builder.compile(checkpointer=checkpointer)
