from typing import List, ForwardRef

from fastapi import HTTPException, status
from pyotp import random_base32
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Table
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, backref

from app.comments.models import Comment
from app.db import ModelMixin, Base
from app.videos.models import Video, Votes, History

UserRef = ForwardRef('User')


Subscriptions = Table(
    'subscriptions',
    Base.metadata,
    Column('subscriber_id', Integer, ForeignKey('user.id', ondelete='CASCADE')),
    Column('subscription_id', Integer, ForeignKey('user.id', ondelete='CASCADE')),
)


class Verification(Base, ModelMixin):
    """ Verification """

    uuid: str = Column(String)
    user_id: int = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return f'Verification № {self.id}'


class User(Base, ModelMixin):
    """ User model """

    username: str = Column(String, unique=True, nullable=False)
    email: str = Column(String, unique=True, nullable=False)
    is_superuser: bool = Column(Boolean, default=False)
    is_active: bool = Column(Boolean, default=False)
    password: str = Column(String, nullable=False)
    avatar: str = Column(String, nullable=True, default='')
    about: str = Column(String(255), nullable=False)
    send_message: bool = Column(Boolean, default=True)
    otp_secret: str = Column(String, default=random_base32)
    two_auth: bool = Column(Boolean, default=False)

    verifications: List[Verification] = relationship(Verification, backref='user', lazy='dynamic')
    subscriptions: List[UserRef] = relationship(
        'User',
        secondary=Subscriptions,
        primaryjoin=lambda: User.id == Subscriptions.c.subscriber_id,
        secondaryjoin=lambda: User.id == Subscriptions.c.subscription_id,
        backref=backref('subscribers', lazy='dynamic'),
        lazy='dynamic'
    )
    videos: List[Video] = relationship(Video, backref='related_user')
    votes: List[Votes] = relationship(Votes, backref='related_user')
    history: List[History] = relationship(History, backref='related_user')
    comments: List[Comment] = relationship(Comment, backref='related_user')

    def __str__(self):
        return f'{self.username}'

    def __repr__(self):
        return f'User {self.username}'

    async def is_following(self, db: AsyncSession, user: UserRef) -> bool:
        """
            Is following to user
            :param db: DB
            :type db: AsyncSession
            :param user: User
            :type user: User
            :return: User is following to user?
            :rtype: bool
        """
        return bool(list(await db.execute(self.subscriptions.filter(Subscriptions.c.subscription_id == user.id))))

    async def follow(self, db: AsyncSession, user: UserRef):
        """
            Follow
            :param db: DB
            :type db: AsyncSession
            :param user: User
            :type user: User
            :return: None
        """
        if not await self.is_following(db, user):
            return self.subscriptions.append(user)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You are already followed')

    async def unfollow(self, db: AsyncSession, user: UserRef):
        """
            Unfollow
            :param db: DB
            :type db: AsyncSession
            :param user: User
            :type user: User
            :return: None
        """
        if await self.is_following(db, user):
            return self.subscriptions.remove(user)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You are already unfollowed')
