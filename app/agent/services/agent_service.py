import json
import logging
from typing import AsyncGenerator, Any, Dict
from uuid import uuid4

from langchain_core.messages import AnyMessage
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langgraph.graph.state import CompiledStateGraph

from app.agent.services.events import ErrorEvent
from app.agent.services.stream_processor import StreamProcessor
from app.agent.utils.utils import langchain_to_chat_message
from app.http.responses import ChatHistory
from app.models import User, Thread

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, graph: CompiledStateGraph):
        self.langfuse = Langfuse(
            debug=False,
            # blocked_instrumentation_scopes=["sqlalchemy", "opentelemetry.instrumentation.fastapi"],
        )

        self.graph = graph
        self.stream_processor = StreamProcessor()

    async def stream_response(self, message: str, thread: Thread, user: User) -> AsyncGenerator[Dict[str, Any], None]:
        with self.langfuse.start_as_current_span(name=self.graph.name) as span:
            run_id = uuid4()

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
                callbacks=[CallbackHandler()],
            )

            try:
                stream = self.graph.astream(
                    inputs,
                    stream_mode=["updates", "messages", "custom"],
                    config=config
                )
                async for event in self.stream_processor.process_stream(stream, run_id, span):
                    yield event.model_dump()
            except Exception as e:
                yield ErrorEvent(
                    data=json.dumps({'run_id': str(run_id), 'content': str(e)})
                ).model_dump()

    async def load_history(self, thread: Thread, user: User) -> ChatHistory:
        """Load chat history for a given thread and user. This is only for demo purposes.
        In production, you would typically fetch this from a database from a separate custom hostory table.
        """
        state_snapshot = await self.graph.aget_state(
            config=RunnableConfig(configurable={"thread_id": thread.id, "user_id": user.id}),
        )

        if not "messages" in state_snapshot.values:
            return ChatHistory(messages=[])

        messages: list[AnyMessage] = state_snapshot.values["messages"]
        chat_messages: list[Any] = [langchain_to_chat_message(m) for m in messages]
        return ChatHistory(messages=chat_messages)

    async def add_feedback(self, trace: str, feedback: float, thread: Thread, user: User) -> Dict[str, str]:
        """TODO: Need to figure out how to pass trace_id from history!!."""
        try:
            self.langfuse.create_score(
                trace_id=trace,
                name="user_feedback",
                value=feedback,
                data_type="NUMERIC"
            )
            return {"status": "success", "message": "Feedback recorded successfully."}
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return {"status": "error", "message": "Failed to record feedback."}
