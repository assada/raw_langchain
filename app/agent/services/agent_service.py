import inspect
import json
import logging
from typing import Any
from typing import AsyncGenerator, Dict

from langchain_core.messages import AnyMessage
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk
from langchain_core.runnables import RunnableConfig
from langgraph.types import Interrupt

from app.agent.graph.graph import Graph
from app.agent.utils.utils import remove_tool_calls, langchain_to_chat_message, convert_message_content_to_string
from app.http.responses import ChatHistory
from app.models import User, Thread

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, graph: Graph):
        self.graph = graph

    def _create_ai_message(parts: dict) -> AIMessage:
        sig = inspect.signature(AIMessage)
        valid_keys = set(sig.parameters)
        filtered = {k: v for k, v in parts.items() if k in valid_keys}
        return AIMessage(**filtered)

    async def stream_response(self, message: str, thread: Thread, user: User) -> AsyncGenerator[Dict[str, Any], None]:

        config = {
            "configurable": {
                "user_id": user.id,
                "thread_id": thread.id
            }
        }
        inputs = {"messages": [HumanMessage(content=message)]}

        try:
            async for stream_event in self.graph.astream(inputs, config=config,
                                                         stream_mode=["updates", "messages", "custom"]):
                logger.debug(f"Chunk: {stream_event}")

                if not isinstance(stream_event, tuple):
                    continue
                stream_mode, event = stream_event
                new_messages = []

                if stream_mode == "updates":
                    for node, updates in event.items():
                        if node == "__interrupt__":
                            interrupt: Interrupt
                            for interrupt in updates:
                                new_messages.append(AIMessage(content=interrupt.value))
                            continue
                        updates = updates or {}
                        update_messages = updates.get("messages", [])
                        new_messages.extend(update_messages)

                if stream_mode == "custom":
                    new_messages = [event]

                processed_messages = []
                current_message: dict[str, Any] = {}
                for message in new_messages:
                    if isinstance(message, tuple):
                        key, value = message
                        current_message[key] = value
                    else:
                        if current_message:
                            processed_messages.append(self._create_ai_message(current_message))
                            current_message = {}
                        processed_messages.append(message)

                if current_message:
                    processed_messages.append(self._create_ai_message(current_message))

                for message in processed_messages:
                    try:
                        chat_message = langchain_to_chat_message(message)
                    except Exception as e:
                        logger.error(f"Error parsing message: {e}")
                        yield {
                            "event": "error",
                            "data": json.dumps({"content": "Unexpected error"})
                        }
                        continue
                    if chat_message.type == "human_message" and chat_message.content == message:
                        continue
                    yield {
                        "event": chat_message.type,
                        "data": chat_message.model_dump_json()
                    }

                if stream_mode == "messages":
                    msg, metadata = event
                    if "skip_stream" in metadata.get("tags", []):
                        continue
                    if not isinstance(msg, AIMessageChunk):
                        continue
                    content = remove_tool_calls(msg.content)
                    if content:
                        yield {
                            "event": "token",
                            "data": json.dumps({"type": "token", "content": convert_message_content_to_string(content)})
                        }
            yield {
                "event": "stream_end",
                "data": json.dumps({'status': 'completed'})
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"content": str(e)})
            }

    async def load_history(self, thread: Thread, user: User) -> ChatHistory:
        state_snapshot = self.graph.get_state(
            config=RunnableConfig(configurable={"thread_id": thread.id, "user_id": user.id}),
        )

        if not "messages" in state_snapshot.values:
            return ChatHistory(messages=[])

        messages: list[AnyMessage] = state_snapshot.values["messages"]
        chat_messages: list[Any] = [langchain_to_chat_message(m) for m in messages]
        return ChatHistory(messages=chat_messages)
