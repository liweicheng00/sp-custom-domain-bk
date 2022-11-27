from pydantic import BaseModel


class WsMessage(BaseModel):
    message: str
    data: list
