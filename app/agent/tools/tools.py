from typing import Any, Callable, List


async def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


TOOLS: List[Callable[..., Any]] = [get_weather]