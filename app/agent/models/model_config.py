from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    prompt: ChatPromptTemplate
    model: str = Field(
        description="Name of the model to use.",
        examples=["openai/gpt-3.5-turbo", "openai/gpt-4"],
    )
    max_tokens: int = Field(
        default=4096,
        description="Maximum number of tokens to generate in the chat completion.",
        examples=[1024, 2048, 4096],
    )
    temperature: float = Field(
        default=0.7,
        description="Sampling temperature to use for the model.",
        ge=0.0,
        le=1.0,
        examples=[0.5, 0.7, 1.0],
    )
