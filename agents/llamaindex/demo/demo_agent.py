from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from llama_index.core.agent.workflow import BaseWorkflowAgent, ReActAgent
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.workflow import Event
from workflows.handler import WorkflowHandler

from app.agent.prompt import Prompt, PromptProvider
from app.agent.services.events import EndEvent, ErrorEvent, TokenEvent
from app.agent.services.events.base_event import BaseEvent
from app.models import Thread, User

from .tools import TOOLS

logger = logging.getLogger(__name__)


class DemoLlamaIndexAgent:
    def __init__(
        self, 
        prompt_provider: PromptProvider,
        custom_settings: dict[str, Any] | None = None
    ):
        self.prompt_provider = prompt_provider
        self.custom_settings = custom_settings or {}
        self.agent: BaseWorkflowAgent | None = None
        
    def _get_model(self, prompt: Prompt) -> FunctionCallingLLM:
        from llama_index.llms.openai import OpenAI
        
        config = getattr(prompt, "config", {}) or {}
        model_config = config.get("model", "openai/gpt-4o-mini")
        
        if "/" in model_config:
            provider, model = model_config.split("/", 1)
        else:
            provider, model = "openai", model_config

        if provider == "openai":
            return OpenAI(
                model=model,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 4096),
                streaming=True
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _get_prompt_fallback(self) -> Prompt:
        return Prompt(
            content="You are a helpful AI assistant with access to tools. Use the tools when needed to answer user questions.",
            config={
                "model": "openai/gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 4096,
            },
        )
    
    def _initialize_agent(self) -> BaseWorkflowAgent:
        if self.agent is not None:
            return self.agent
            
        prompt = self.prompt_provider.get_prompt(
            "demo_llamaindex_agent", "production", self._get_prompt_fallback()
        )
        
        llm = self._get_model(prompt)

        self.agent = ReActAgent(
            tools=TOOLS,
            llm=llm,
            verbose=self.custom_settings.get("verbose", True),
            system_prompt=prompt.content
        )
        
        return self.agent
    
    async def stream_response(
        self, message: str, thread: Thread, user: User
    ) -> AsyncGenerator[dict[str, Any]]:
        try:
            agent = self._initialize_agent()
            handler = agent.run(user_msg=message)

            async def get_result() -> WorkflowHandler:
                return await handler
            
            run_task = asyncio.create_task(get_result())

            streaming_content = ""
            has_content = False

            async for event in agent.stream_events():
                processed_event = self._process_workflow_event(event, thread, user)
                if processed_event:
                    if isinstance(processed_event, TokenEvent):
                        token_data = json.loads(processed_event.data)
                        streaming_content += token_data.get("content", "")
                        has_content = True
                    
                    yield processed_event.model_dump()

            final_response = await run_task

            if not has_content and final_response:
                message_event = BaseEvent.from_payload(
                    event="message",
                    payload={
                        "type": "ai_message",
                        "content": str(final_response),
                        "metadata": {
                            "agent": "demo_llamaindex_agent",
                            "framework": "llamaindex", 
                            "user_id": str(user.id),
                            "thread_id": str(thread.id)
                        }
                    }
                )
                yield message_event.model_dump()
            
        except Exception as e:
            logger.error(f"Error in LlamaIndex agent streaming: {e}")
            error_event = ErrorEvent(
                data=json.dumps({
                    "content": f"Error processing request: {str(e)}",
                    "error_type": type(e).__name__
                })
            )
            yield error_event.model_dump()
        finally:
            end_event = EndEvent(data=json.dumps({"status": "completed"}))
            yield end_event.model_dump()
    
    def _process_workflow_event(self, event: Event, thread: Thread, user: User) -> BaseEvent | None:
        """Process workflow events and convert to our event format."""
        try:
            event_type = type(event).__name__
            
            if hasattr(event, 'delta') and event.delta:
                return TokenEvent(
                    data=json.dumps({
                        "content": str(event.delta),
                        "metadata": {
                            "agent": "demo_llamaindex_agent",
                            "framework": "llamaindex",
                            "event_type": event_type
                        }
                    })
                )
            
            elif hasattr(event, 'content') and event.content:
                return BaseEvent.from_payload(
                    event="message",
                    payload={
                        "type": "ai_message", 
                        "content": str(event.content),
                        "metadata": {
                            "agent": "demo_llamaindex_agent",
                            "framework": "llamaindex",
                            "event_type": event_type,
                            "user_id": str(user.id),
                            "thread_id": str(thread.id)
                        }
                    }
                )
            
            elif hasattr(event, 'tool_calls') and event.tool_calls:
                return BaseEvent.from_payload(
                    event="tool_call",
                    payload={
                        "tool_calls": [str(call) for call in event.tool_calls],
                        "metadata": {
                            "agent": "demo_llamaindex_agent",
                            "framework": "llamaindex",
                            "event_type": event_type
                        }
                    }
                )
            
            else:
                logger.debug(f"Workflow event {event_type}: {event}")
                return None
                
        except Exception as e:
            logger.warning(f"Error processing workflow event: {e}")
            return None
    
    async def load_history(
        self, thread: Thread, user: User
    ) -> AsyncGenerator[dict[str, Any]]:
        """Load conversation history."""
        # For demo purposes, return empty history
        # In real implementation, you'd load from agent's chat history
        logger.info(f"Loading history for thread {thread.id} with LlamaIndex agent")
        
        end_event = EndEvent(data=json.dumps({"status": "completed", "message": "No history available"}))
        yield end_event.model_dump()