import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Dict, List, cast, TypeVar, Generic

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langfuse import Langfuse
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.agent.graph.base_state import BaseState
from app.agent.utils.utils import load_chat_model

logger = logging.getLogger(__name__)

StateType = TypeVar('StateType', bound=BaseState)


class Graph(ABC, Generic[StateType]):
    def __init__(self, checkpointer: BaseCheckpointSaver, langfuse: Langfuse):
        self._checkpointer = checkpointer
        self._langfuse = langfuse

    @property
    @abstractmethod
    def graph_name(self) -> str:
        """Name of the graph for prompt retrieval."""
        pass

    @abstractmethod
    def build_graph(self):
        """Build the StateGraph for the agent."""
        pass

    def get_prompt_name(self) -> str:
        """Get the prompt name for Langfuse. Override if different from graph_name."""
        return self.graph_name

    def get_prompt_label(self) -> str:
        """Get the prompt label for Langfuse."""
        return "production"

    def get_prompt_fallback(self) -> str:
        """Get the fallback prompt text."""
        return "You are a helpful assistant."

    def get_default_model(self) -> str:
        """Get the default model name."""
        return "openai/gpt-4o-mini"

    def get_default_temperature(self) -> float:
        """Get the default temperature."""
        return 1.0

    def get_tools(self) -> List:
        """Get tools for the model. Override to provide specific tools."""
        return []

    def get_prompt_placeholders(self) -> Dict[str, str]:
        """Get placeholder variables for prompt template. Override to add more."""
        return {"system_time": datetime.now(tz=UTC).isoformat()}

    def is_emergency_stop_needed(self, state: StateType, response: AIMessage) -> bool:
        """Check if emergency stop is needed. Override for custom emergency stop logic."""
        return (
                hasattr(state, 'is_last_step') and
                getattr(state, 'is_last_step', False) and
                response.tool_calls
        )

    def create_emergency_response(self, response: AIMessage) -> AIMessage:
        """Create emergency response when max steps reached but model still wants to call tools."""
        return AIMessage(
            id=response.id,
            content="Sorry, I could not find an answer to your question in the specified number of steps.",
        )

    async def call_model(self, state: StateType, config: RunnableConfig) -> Dict[str, List[AIMessage]]:
        """Base implementation of call_model. Can be overridden if needed."""
        langfuse_prompt = self._langfuse.get_prompt(
            self.get_prompt_name(),
            label=self.get_prompt_label(),
            fallback=self.get_prompt_fallback()
        )

        model = load_chat_model(  # TODO: Reimplement this
            langfuse_prompt.config.get("model", self.get_default_model()),
            temperature=langfuse_prompt.config.get("temperature", self.get_default_temperature())
        )

        tools = self.get_tools()
        if tools:
            model = model.bind_tools(tools)

        prompt = (
            ChatPromptTemplate.from_messages([
                ("system", langfuse_prompt.get_langchain_prompt()),
                MessagesPlaceholder("history"),
            ])
            .partial(**self.get_prompt_placeholders())
        )
        prompt.metadata = {"langfuse_prompt": langfuse_prompt}

        chain = prompt | model
        response = cast(
            AIMessage,
            await chain.ainvoke(
                {"history": state.messages},
                config=config, # TODO: Pass handler here?
            ),
        )

        if self.is_emergency_stop_needed(state, response):
            response = self.create_emergency_response(response)

        return {
            "messages": [response],
            "message_trace_map": [*state.message_trace_map, {
                "id": response.id,
                "trace_id": self._langfuse.get_current_trace_id(),
            }]
        }
