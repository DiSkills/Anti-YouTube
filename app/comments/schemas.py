from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic.typing import ForwardRef

from app.auth.schemas import UserPublic

GetCommentRef = ForwardRef('GetComment')


class CreateComment(BaseModel):
    """ Create comment """

    text: str
    video_id: int
    parent_id: Optional[int] = None


class GetComment(BaseModel):
    """ Get comment """

    id: int
    text: str
    user: UserPublic
    created_at: datetime
    is_child: bool
    parent: Optional[GetCommentRef]


GetComment.update_forward_refs()
