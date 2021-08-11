from typing import Optional, List

from pydantic import BaseModel


class Message(BaseModel):
    """
        Message
        :type msg: str
    """

    msg: str


class Votes(BaseModel):
    """
        Votes
        :type likes: int
        :type dislikes: int
    """

    likes: int
    dislikes: int


class Paginate(BaseModel):
    """
        Paginate
        :type page: int
        :type previous: Optional[str]
        :type next: Optional[str]
        :type results: List
    """

    page: int
    previous: Optional[str]
    next: Optional[str]
    results: List
