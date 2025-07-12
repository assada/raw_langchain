from pydantic import BaseModel


class CustomUIMessage(BaseModel):
    type: str
    component: str
    id: str
    params: dict
