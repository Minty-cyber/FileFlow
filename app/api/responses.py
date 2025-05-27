from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

class ExceptionLogResponse(BaseModel):
    id: uuid.UUID = None
    username: Optional[str] = None
    error_message: str
    stack_trace: str
    timestamp: datetime
    path: Optional[str] = None
    method: Optional[str] = None
    client_ip: Optional[str] = None

    class Config:
        orm_mode = True