from datetime import datetime

from sqlalchemy import Column, String, DateTime, BigInteger, Integer, ForeignKey

from app.db import Base, ModelMixin


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
