import base64
import json
from typing import AsyncGenerator
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
from app.models.user import User
from app.models.thread import Thread

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

class AgentService:
    def __init__(self):
        self.agent = create_react_agent(
            model="gpt-4o-mini",
            tools=[get_weather],
            prompt="You are a helpful assistant"
        )
        # checkpointer = InMemorySaver()
        # self.agent = self.agent.compile(checkpointer=checkpointer)
    
    async def stream_response(self, message: str, thread: Thread, user: User) -> AsyncGenerator[str, None]:
        
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
                                            tool_call_data = {
                                                "name": tc.get("name", ""),
                                                "args": tc.get("args", {}),
                                                "id": tc.get("id", "")
                                            }
                                            yield f"event: tool_call\ndata: {json.dumps(tool_call_data)}\n\n"
                                    
                                    if getattr(msg, 'content', ''):
                                        content_data = {"content": msg.content}
                                        yield f"event: ai_message\ndata: {json.dumps(content_data)}\n\n"
                                
                                elif msg_type == "ToolMessage":
                                    tool_result_data = {
                                        "tool_name": getattr(msg, 'name', ''),
                                        "content": getattr(msg, 'content', ''),
                                        "tool_call_id": getattr(msg, 'tool_call_id', '')
                                    }
                                    yield f"event: tool_result\ndata: {json.dumps(tool_result_data)}\n\n"
            
            yield f"event: stream_end\ndata: {json.dumps({'status': 'completed'})}\n\n"
                                    
        except Exception as e:
            error_data = {"content": str(e)}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n" 