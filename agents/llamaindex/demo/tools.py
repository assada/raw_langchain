
from llama_index.core.tools import FunctionTool


async def get_weather(city: str) -> str:
    """Get weather for a given city.
    
    Args:
        city: The name of the city to get weather for
        
    Returns:
        Weather information for the city
    """
    # For demo purposes, return mock weather data
    # In real implementation, this would call a weather API
    import random
    weather_conditions = ["sunny", "cloudy", "rainy", "snowy", "partly cloudy"]
    temperature = random.randint(-5, 35)
    condition = random.choice(weather_conditions)
    
    return f"The weather in {city} is {condition} and {temperature}°C!"


def create_weather_tool() -> FunctionTool:
    return FunctionTool.from_defaults(
        fn=get_weather,
        name="get_weather",
        description="Get current weather information for a specific city"
    )


TOOLS = [create_weather_tool()]