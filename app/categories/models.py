from typing import List

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db import Base, ModelMixin
from app.videos.models import Video


class Category(Base, ModelMixin):
    """ Category """

    name: str = Column(String)

    videos: List[Video] = relationship(Video, backref='category', lazy='dynamic')

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return f'Category {self.name}'
