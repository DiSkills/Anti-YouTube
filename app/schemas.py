from typing import Optional, List

from pydantic import BaseModel


class Message(BaseModel):
    """ Message """

    msg: str


class Votes(BaseModel):
    """ Votes """

    likes: int
    dislikes: int


class Paginate(BaseModel):
    """ Paginate """

    page: int
    previous: Optional[str]
    next: Optional[str]
    results: List
