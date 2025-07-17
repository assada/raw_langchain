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
        self.callbacks = []
        self.stream_processor = StreamProcessor()

    async def stream_response(self, message: str, thread: Thread, user: User) -> AsyncGenerator[Dict[str, Any], None]:
        run_id = uuid4()

        self.callbacks.extend([CallbackHandler()])

        config = RunnableConfig(
            configurable={
                "user_id": user.id,
                "thread_id": thread.id,
            },
            run_id=run_id,
            callbacks=self.callbacks
        )

        inputs = {"messages": [HumanMessage(content=message)]}

        try:
            stream = self.graph.astream(
                inputs,
                config=config,
                stream_mode=["updates", "messages", "custom"]
            )
            async for event in self.stream_processor.process_stream(stream, run_id):
                yield event.model_dump()
        except Exception as e:
            yield ErrorEvent(
                data=json.dumps({'run_id': str(run_id), 'content': str(e)})
            ).model_dump()

    async def load_history(self, thread: Thread, user: User) -> ChatHistory:
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
