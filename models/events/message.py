from pydantic import BaseModel


class MessageEvent(BaseModel):
    user_id: int
    text: str
    peer_id: int
    conversation_message_id: int
    id: int
    from_id: int
    date: int
