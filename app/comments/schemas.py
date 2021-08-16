from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from pydantic.typing import ForwardRef

from app.auth.schemas import UserPublic

GetCommentRef = ForwardRef('GetComment')
GetAllCommentsForward = ForwardRef('GetAllComments')


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
    parent_id: Optional[int]


class GetCommentParent(GetComment):
    """ Get comment with parent """

    parent: Optional[GetCommentRef]


class GetAllComments(GetComment):
    """ Get comments tree """

    children: Optional[List[GetAllCommentsForward]]


GetComment.update_forward_refs()
GetAllComments.update_forward_refs()
