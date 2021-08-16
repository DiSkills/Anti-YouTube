from datetime import datetime
from typing import ForwardRef, List

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship, backref

from app.db import Base, ModelMixin

User = ForwardRef('User')
Video = ForwardRef('Video')
CommentRef = ForwardRef('Comment')


CommentChildren = Table(
    'comment_children',
    Base.metadata,
    Column('parent_id', Integer, ForeignKey('comment.id', ondelete='CASCADE')),
    Column('children_id', Integer, ForeignKey('comment.id', ondelete='CASCADE')),
)


class Comment(Base, ModelMixin):
    """ Comment """

    text: str = Column(String(200))
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    is_child: bool = Column(Boolean, default=False)

    user_id: int = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    video_id: int = Column(Integer, ForeignKey('video.id', ondelete='CASCADE'))

    user: User = relationship('User', backref='related_comments')
    video: Video = relationship('Video', backref='related_comments')
    children = relationship(
        'Comment',
        secondary=CommentChildren,
        primaryjoin=lambda: Comment.id == CommentChildren.c.parent_id,
        secondaryjoin=lambda: Comment.id == CommentChildren.c.children_id,
        backref=backref('parent', lazy='dynamic'),
        lazy='dynamic'
    )

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return f'Comment {self.id}'
