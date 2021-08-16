from datetime import datetime
from typing import List

from pydantic import BaseModel, validator

from app.auth.schemas import UserPublic
from app.categories.schemas import GetCategory
from app.schemas import Paginate, Votes


class VideoBase(BaseModel):
    """ Video base """

    title: str
    description: str


class CreateVideo(VideoBase):
    """ Create video """

    category_id: int


class VideoUpdate(VideoBase):
    """ Update video """

    category_id: int


class GetVideoBase(VideoBase):
    """ Get video base """

    id: int
    video_file: str
    preview_file: str
    created_at: datetime
    views: int


class GetVideoNotUser(GetVideoBase):
    """ Get video """

    category: GetCategory
    votes: Votes


class GetVideo(GetVideoNotUser):
    """ Get video """

    user: UserPublic


class SubscriptionsVideos(BaseModel):
    """ Subscriptions videos """

    user: UserPublic
    videos: List[GetVideo]


class VideoPaginate(Paginate):
    """ Video paginate """

    results: List[GetVideo]


class CreateVote(BaseModel):
    """ Create votes """

    vote: int
    video_id: int

    @validator('vote')
    def validate_vote(cls, vote):
        if vote < 0 or vote > 1:
            raise ValueError('Vote is 0 (dislike) or 1 (like)')
        return vote


class UpdateVideoViews(BaseModel):
    """ Update video """

    views: int


class CreateHistory(BaseModel):
    """ Create history """

    user_id: int
    video_id: int
