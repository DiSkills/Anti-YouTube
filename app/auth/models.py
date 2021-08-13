from typing import List, ForwardRef

from fastapi import HTTPException, status
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Table
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, backref

from app.db import ModelMixin, Base

UserRef = ForwardRef('User')


Subscriptions = Table(
    'subscriptions',
    Base.metadata,
    Column('subscriber_id', Integer, ForeignKey('user.id', ondelete='CASCADE')),
    Column('subscription_id', Integer, ForeignKey('user.id', ondelete='CASCADE')),
)


class Verification(Base, ModelMixin):
    """
        Verification
        :type uuid: str
        :type user_id: int
    """

    uuid: str = Column(String)
    user_id: int = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return f'Verification № {self.id}'


class User(Base, ModelMixin):
    """
        User model
        :type username: str
        :type email: str
        :type is_superuser: bool
        :type is_active: bool
        :type password: str
        :type avatar: str
        :type about: str
        :type send_message: bool
    """

    username: str = Column(String, unique=True, nullable=False)
    email: str = Column(String, unique=True, nullable=False)
    is_superuser: bool = Column(Boolean, default=False)
    is_active: bool = Column(Boolean, default=False)
    password: str = Column(String, nullable=False)
    avatar: str = Column(String, nullable=True, default='')
    about: str = Column(String(255), nullable=False)
    send_message: bool = Column(Boolean, default=True)

    verifications: List[Verification] = relationship(Verification, backref='user', lazy='dynamic')
    subscriptions = relationship(
        'User',
        secondary=Subscriptions,
        primaryjoin=lambda: User.id == Subscriptions.c.subscriber_id,
        secondaryjoin=lambda: User.id == Subscriptions.c.subscription_id,
        backref=backref('subscribers', lazy='dynamic'),
        lazy='dynamic'
    )

    def __str__(self):
        return f'{self.username}'

    def __repr__(self):
        return f'User {self.username}'

    async def is_following(self, db: AsyncSession, user):
        """Is following user"""
        return bool(list(await db.execute(self.subscriptions.filter(Subscriptions.c.subscription_id == user.id))))

    async def follow(self, db: AsyncSession, user: UserRef):
        if not await self.is_following(db, user):
            return self.subscriptions.append(user)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You are already followed')

    async def unfollow(self, db: AsyncSession, user: UserRef):
        if await self.is_following(db, user):
            return self.subscriptions.remove(user)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You are already unfollowed')
