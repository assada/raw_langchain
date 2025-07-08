import json
from typing import AsyncGenerator, Dict, Any
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage

from app.bootstrap.config import AppConfig
from app.models import User, Thread
from app.agent.models import ToolCall, AIMessage, ToolResult


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

class AgentService:
    def __init__(self, config: AppConfig):
        self.agent = create_react_agent(
            model=config.agent_model,
            tools=[get_weather],
            prompt=config.agent_prompt
        )
        # checkpointer = InMemorySaver()
        # self.agent = self.agent.compile(checkpointer=checkpointer)
    
    async def stream_response(self, message: str, thread: Thread, user: User) -> AsyncGenerator[Dict[str, Any], None]:
        
        config = {"configurable": {"user_id": user.id, "thread_id": thread.id}}
        inputs = {"messages": [HumanMessage(content=message)]}

        try:
            for mode, chunk in self.agent.stream(inputs, config=config, stream_mode=["updates", "custom"]):
                if isinstance(chunk, dict):
                    for key, value in chunk.items():
                        if isinstance(value, dict) and "messages" in value:
                            for msg in value["messages"]:
                                msg_type = type(msg).__name__
                                
                                if msg_type == "AIMessage":
                                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                        for tc in msg.tool_calls:
                                            yield {
                                                "event": "tool_call",
                                                "data": ToolCall(
                                                            name=tc.get("name", ""),
                                                            args=tc.get("args", {}),
                                                            id=tc.get("id", "")
                                                        ).model_dump_json()
                                            }
                                    
                                    if getattr(msg, 'content', ''):
                                        yield {
                                            "event": "ai_message",
                                            "data": AIMessage(content=msg.content).model_dump_json()
                                        }
                                
                                elif msg_type == "ToolMessage":
                                    yield {
                                        "event": "tool_result",
                                        "data": ToolResult(
                                                    tool_name=getattr(msg, 'name', ''),
                                                    content=getattr(msg, 'content', ''),
                                                    tool_call_id=getattr(msg, 'tool_call_id', '')
                                                ).model_dump_json()
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
