from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: Optional[str] = Field(
        None,
        description="For some errors that could be handled programmatically, a short string indicating the error code reported.",
    )
    message: Optional[str] = Field(
        None, description="A human-readable short description of the error."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="A dictionary of additional information about the error."
    )
