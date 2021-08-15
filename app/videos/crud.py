from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.CRUD import CRUD, ModelType
from app.videos.models import Video
from app.videos.schemas import CreateVideo, VideoUpdate


class VideoCRUD(CRUD[Video, CreateVideo, VideoUpdate]):
    """ Video CRUD """

    async def filter(self, db: AsyncSession, **kwargs) -> List[ModelType]:
        """
            Filter
            :param db: DB
            :type db: AsyncSession
            :param kwargs: kwargs
            :return: Models
            :rtype: list
        """
        query = await db.execute(select(self.model).options(
            selectinload(self.model.category), selectinload(self.model.user)
        ).order_by(self.model.id.desc()).filter_by(**kwargs))
        return query.scalars()

    async def get(self, db: AsyncSession, **kwargs) -> Optional[ModelType]:
        """
            Get
            :param db: DB
            :type db: AsyncSession
            :param kwargs: kwargs
            :return: Model
            :rtype: ModelType
        """
        query = await db.execute(
            select(self.model).options(
                selectinload(self.model.category), selectinload(self.model.user)
            ).filter_by(**kwargs)
        )
        return query.scalars().first()

    async def all(self, db: AsyncSession,  skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
            All
            :param db: DB
            :type db: AsyncSession
            :param skip: start
            :type skip: int
            :param limit: end
            :type limit: int
            :return: All ModelType
            :rtype: list
        """
        query = await db.execute(
            select(self.model).options(
                selectinload(self.model.category), selectinload(self.model.user)
            ).order_by(self.model.id.desc()).offset(skip).limit(limit)
        )
        return query.scalars().all()


video_crud = VideoCRUD(Video)
