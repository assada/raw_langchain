from pydantic import BaseModel


class FeedbackRequest(BaseModel):
    trace_id: str
    feedback: int
