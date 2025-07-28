from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str | None = Field(
        None,
        description="For some errors that could be handled programmatically, a short string indicating the error code reported.",
    )
    message: str | None = Field(
        None, description="A human-readable short description of the error."
    )
    metadata: dict[str, Any] | None = Field(
        None, description="A dictionary of additional information about the error."
    )
