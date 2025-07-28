from collections.abc import Callable
from typing import Any

from langgraph.config import get_stream_writer

from app.agent.models import CustomUIMessage


async def get_weather(city: str) -> str:
    """Get weather for a given city."""

    writer = get_stream_writer()
    if writer is not None:
        writer(
            CustomUIMessage(
                type="ui",
                component="file_upload",
                id="doc-upload",
                params={
                    "label": "Upload weather data",
                    "accept": ["application/json"],
                    "placeholder": f"Upload a JSON file with weather data for the {city} city.",
                },
            )
        )

    return f"It's always sunny in {city}!"


TOOLS: list[Callable[..., Any]] = [get_weather]
