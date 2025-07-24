import json
import logging
from datetime import datetime, UTC
from typing import AsyncGenerator, Any, Dict
from uuid import uuid4

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langfuse import Langfuse
from langgraph.graph.state import CompiledStateGraph

from app.agent.services.events import ErrorEvent, EndEvent
from app.agent.services.events.base_event import BaseEvent
from app.agent.services.stream_processor import StreamProcessor
from app.agent.utils.utils import langchain_to_chat_message
from app.models import User, Thread
from app.models.thread import ThreadStatus

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, graph: CompiledStateGraph, langfuse: Langfuse):
        self.langfuse = langfuse
        self.graph = graph
        self.stream_processor = StreamProcessor()

    async def stream_response(self, message: str, thread: Thread, user: User) -> AsyncGenerator[Dict[str, Any], None]:
        with self.langfuse.start_as_current_span(name=self.graph.name) as span:
            run_id = uuid4()

            thread.status = ThreadStatus.busy
            thread.updated_at = datetime.now(UTC)

            inputs = {
                "messages": [HumanMessage(content=message)],
            }

            config = RunnableConfig(
                configurable={
                    "thread_id": thread.id,
                    "user_id": user.id,
                },
                metadata={
                    "langfuse_session_id": str(thread.id),
                    "langfuse_user_id": str(user.id),
                    "langfuse_tags": ["production", "chat-bot"],
                },
                run_id=run_id,
            )

            try:
                stream = self.graph.astream(
                    inputs,
                    stream_mode=["updates", "messages", "custom"],
                    config=config
                )
                async for event in self.stream_processor.process_stream(stream, run_id, span):
                    thread.status = ThreadStatus.idle
                    yield event.model_dump()
            except Exception as e:
                thread.status = ThreadStatus.error
                yield ErrorEvent(
                    data=json.dumps({'run_id': str(run_id), 'content': str(e)})
                ).model_dump()

    async def load_history(self, thread: Thread, user: User) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            state_snapshot = await self.graph.aget_state(
                config=RunnableConfig(configurable={"thread_id": thread.id, "user_id": user.id}),
            )

            trace_by_id = {m["id"]: m["trace_id"] for m in state_snapshot.values.get("message_trace_map", [])}

            messages = state_snapshot.values.get("messages", [])
            if not messages:
                yield EndEvent(data=json.dumps({"status": "completed"})).model_dump()
                return

            for m in messages:
                chat_msg = langchain_to_chat_message(m, trace_id=trace_by_id.get(m.id))

                event = BaseEvent.from_payload(
                    event=chat_msg.type,
                    payload=chat_msg.model_dump(),
                    source="history"
                )

                yield event.model_dump()

            yield EndEvent(data=json.dumps({"status": "completed"})).model_dump()

        except Exception as e:
            logger.error(f"Error loading history: {e}")
            yield ErrorEvent(
                data=json.dumps({"content": f"Error loading history: {str(e)}"})
            ).model_dump()

    async def add_feedback(self, trace: str, feedback: float, thread: Thread, user: User) -> Dict[str, str]:
        try:
            self.langfuse.create_score(
                trace_id=trace,
                name="user_feedback",
                value=feedback,
                data_type="NUMERIC"
            )
            thread.updated_at = datetime.now(UTC)
            return {"status": "success", "message": "Feedback recorded successfully."}
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return {"status": "error", "message": "Failed to record feedback."}
