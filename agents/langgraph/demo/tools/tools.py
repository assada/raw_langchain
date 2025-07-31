from collections.abc import Callable
from typing import Any

from app.agent.models import CustomUIMessage
from langgraph.config import get_stream_writer


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

    import random

    weather_conditions = ["sunny", "cloudy", "rainy", "snowy", "partly cloudy"]
    temperature = random.randint(-5, 35)
    condition = random.choice(weather_conditions)

    return f"The weather in {city} is {condition} and {temperature}°C!"


TOOLS: list[Callable[..., Any]] = [get_weather]
