from typing import List

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db import ModelMixin, Base


class Verification(Base, ModelMixin):
    """
        Verification

    """

    uuid: str = Column(String)
    user_id: int = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))


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
