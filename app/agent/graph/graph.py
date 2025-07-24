import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Dict, List, cast, TypeVar, Generic

import llm_guard
from langchain.chains.base import Chain
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig, RunnableLambda, Runnable, RunnableMap
from langchain_core.runnables import RunnablePassthrough
from langfuse import Langfuse
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.agent.graph.base_state import BaseState
from app.agent.guards import LLMGuardPromptChain
from app.agent.guards.LLMGuard import LLMGuardOutputChain
from app.agent.utils.utils import load_chat_model

logger = logging.getLogger(__name__)

StateType = TypeVar('StateType', bound=BaseState)


class Graph(ABC, Generic[StateType]):
    def __init__(self, checkpointer: BaseCheckpointSaver, langfuse: Langfuse):
        self._checkpointer = checkpointer
        self._langfuse = langfuse
        self._vault = llm_guard.vault.Vault()
        self._use_onnx = False  # TODO: Make this configurable
        self.use_output_scanner = False  # TODO: Make this configurable
        self.use_prompt_scanner = False  # TODO: Make this configurable

    def get_guard_prompt_scanner(self) -> Runnable | Chain:
        if not self.use_prompt_scanner:
            return RunnableLambda(lambda d: {"history": d["input"]})
        return LLMGuardPromptChain(
            vault=self._vault,
            scanners={
                "Anonymize": {"use_faker": False, "use_onnx": self._use_onnx},
                "BanSubstrings": {
                    "substrings": ["Laiyer"],
                    "match_type": "word",
                    "case_sensitive": False,
                    "redact": True,
                },
                "BanTopics": {"topics": ["violence"], "threshold": 0.7, "use_onnx": self._use_onnx},
            },
            scanners_ignore_errors=[
                "Anonymize",
                # "BanSubstrings",
            ],  # These scanners redact, so I can skip them from failing the prompt
        )

    def get_guard_output_scanner(self) -> Runnable | Chain:
        if not self.use_output_scanner:
            return RunnablePassthrough()
        return LLMGuardOutputChain(
            vault=self._vault,
            scanners={
                "BanSubstrings": {
                    "substrings": ["Laiyer", "Привіт", "Hello", "сонячно"],
                    "match_type": "word",
                    "case_sensitive": False,
                    "redact": True,
                },
                "BanTopics": {"topics": ["violence"], "threshold": 0.7, "use_onnx": self._use_onnx},
                "Deanonymize": {},
                "Language": {
                    "valid_languages": ["en"],
                    "use_onnx": self._use_onnx,
                },
                "MaliciousURLs": {"threshold": 0.75, "use_onnx": self._use_onnx},
                "Regex": {
                    "patterns": ["Bearer [A-Za-z0-9-._~+/]+"],
                },
                "Sensitive": {"redact": False, "use_onnx": self._use_onnx},
                "Sentiment": {"threshold": -0.05},
                "Toxicity": {"threshold": 0.7, "use_onnx": self._use_onnx},
            },
            scanners_ignore_errors=["BanSubstrings", "Regex", "Sensitive"],
        )

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

        template = (
            ChatPromptTemplate.from_messages([
                ("system", langfuse_prompt.get_langchain_prompt()),
                MessagesPlaceholder("history"),
            ])
            .partial(**self.get_prompt_placeholders())
        )
        template.metadata = {"langfuse_prompt": langfuse_prompt}

        pipeline = (
                self.get_guard_prompt_scanner()
                | template
        )

        model_output = pipeline | model

        output_guard = self.get_guard_output_scanner()

        if isinstance(output_guard, RunnablePassthrough):
            guarded_chain = model_output
        else:
            pack_for_guard = RunnableMap(prompt=pipeline, output=model_output)
            guarded_chain = pack_for_guard | output_guard

        raw_resp = await guarded_chain.ainvoke(
            {"input": state.messages},
            config=config,
        )

        if isinstance(raw_resp, dict):
            raw_resp = raw_resp.get("result", raw_resp)

        response = cast(AIMessage, raw_resp)

        if self.is_emergency_stop_needed(state, response):
            response = self.create_emergency_response(response)

        return {
            "messages": [response],
            "message_trace_map": [*state.message_trace_map, {
                "id": response.id,
                "trace_id": self._langfuse.get_current_trace_id(),
            }]
        }
