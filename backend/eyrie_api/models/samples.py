from pydantic import BaseModel
from typing import Optional

class QCUpdate(BaseModel):
    qc: str
    comments: Optional[str] = ""

class CommentUpdate(BaseModel):
    comments: str
