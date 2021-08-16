from typing import Optional

from pydantic import BaseModel


class CommentBase(BaseModel):
    """ Comment base """
    text: str
    video_id: int


class CreateComment(CommentBase):
    """ Create comment """
    parent_id: Optional[int] = None
