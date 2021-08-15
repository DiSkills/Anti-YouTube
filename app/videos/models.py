from datetime import datetime
from typing import ForwardRef, List

from sqlalchemy import Column, String, DateTime, BigInteger, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base, ModelMixin

Category = ForwardRef('Category')
User = ForwardRef('User')
VotesRef = ForwardRef('Votes')


class Video(Base, ModelMixin):
    """ Video """

    title: str = Column(String(50), nullable=False)
    description: str = Column(String(500), nullable=False)
    video_file: str = Column(String, nullable=False)
    preview_file: str = Column(String, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    views: int = Column(BigInteger, default=0)

    category_id: int = Column(Integer, ForeignKey('category.id', ondelete='CASCADE'))
    user_id: int = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))

    category: Category = relationship('Category', backref='related_videos')
    user: User = relationship('User', backref='related_videos')
    votes: List[VotesRef] = relationship('Votes', backref='related_videos')

    def __str__(self):
        return f'{self.title}'

    def __repr__(self):
        return f'Video {self.title}'


class Votes(Base, ModelMixin):
    """ Votes """

    vote: int = Column(Integer, default=0)
    video_id: int = Column(Integer, ForeignKey('video.id', ondelete='CASCADE'))
    user_id: int = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))

    video: Video = relationship(Video, backref='related_votes')
    user: User = relationship('User', backref='related_votes')

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return f'Votes {self.id}'
