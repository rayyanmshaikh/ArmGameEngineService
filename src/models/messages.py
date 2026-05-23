from pydantic import BaseModel
from typing import Optional


class HumanMoveRequest(BaseModel):
    move: str


class RobotDoneRequest(BaseModel):
    status: str


class FeedbackMessage(BaseModel):
    type: str
    message: str
    turn: Optional[str]
    fen: Optional[str]
