from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.CRUD import CRUD, ModelType
from app.videos.models import Video
from app.videos.schemas import CreateVideo, VideoUpdate


class VideoCRUD(CRUD[Video, CreateVideo, VideoUpdate]):
    """ Video CRUD """

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


video_crud = VideoCRUD(Video)
