import json
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langfuse import Langfuse  # type: ignore[attr-defined]
from langfuse.langchain import CallbackHandler
from langgraph.graph.state import CompiledStateGraph

from app.agent.services.events import EndEvent, ErrorEvent
from app.agent.services.events.base_event import BaseEvent
from app.agent.services.stream_processor import StreamProcessor
from app.agent.utils import to_chat_message
from app.models import Thread, User
from app.models.thread import ThreadStatus

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, graph: CompiledStateGraph[Any, Any, Any], langfuse: Langfuse):
        self.langfuse = langfuse
        self.graph = graph
        self.stream_processor = StreamProcessor()

    async def stream_response(
        self, message: str, thread: Thread, user: User
    ) -> AsyncGenerator[dict[str, Any]]:
        with self.langfuse.start_as_current_span(
            name=self.graph.name, input=message
        ) as span:
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
                    "trace_id": span.trace_id,
                },
                run_id=run_id,
                callbacks=[CallbackHandler()],
            )

            try:
                stream = self.graph.astream(
                    inputs, stream_mode=["updates", "messages", "custom"], config=config
                )
                async for event in self.stream_processor.process_stream(
                    stream, run_id, span # type: ignore[arg-type]
                ):
                    thread.status = ThreadStatus.idle
                    yield event.model_dump()
            except Exception as e:
                thread.status = ThreadStatus.error
                yield ErrorEvent(
                    data=json.dumps({"run_id": str(run_id), "content": str(e)})
                ).model_dump()

    async def load_history(
        self, thread: Thread, user: User
    ) -> AsyncGenerator[dict[str, Any]]:
        try:
            state_snapshot = await self.graph.aget_state(
                config=RunnableConfig(
                    configurable={"thread_id": thread.id, "user_id": user.id}
                ),
            )

            trace_by_id = {
                m["id"]: m["trace_id"]
                for m in state_snapshot.values.get("message_trace_map", [])
            }

            messages = state_snapshot.values.get("messages", [])
            if not messages:
                yield EndEvent(data=json.dumps({"status": "completed"})).model_dump()
                return

            for m in messages:
                chat_msg = to_chat_message(m, trace_id=trace_by_id.get(m.id))

                event = BaseEvent.from_payload(
                    event=chat_msg.type, payload=chat_msg.model_dump(), source="history"
                )

                yield event.model_dump()

            yield EndEvent(data=json.dumps({"status": "completed"})).model_dump()

        except Exception as e:
            logger.error(f"Error loading history: {e}")
            yield ErrorEvent(
                data=json.dumps({"content": f"Error loading history: {str(e)}"})
            ).model_dump()

    async def add_feedback(
        self, trace: str, feedback: float, thread: Thread, user: User
    ) -> dict[str, str]:
        try:
            self.langfuse.create_score(
                trace_id=trace,
                name="user_feedback",
                value=feedback,
                data_type="NUMERIC",
                # session_id=thread.id, # Bug in Langfuse SDK, session_id is broken
                comment="User feedback on the response",
                metadata={
                    "langfuse_user_id": str(user.id),
                },
            )
            thread.updated_at = datetime.now(UTC)
            return {"status": "success", "message": "Feedback recorded successfully."}
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return {"status": "error", "message": "Failed to record feedback."}
