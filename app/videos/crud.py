from typing import Optional, List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.CRUD import CRUD, ModelType
from app.videos.models import Video, Votes, History
from app.videos.schemas import CreateVideo, VideoUpdate, CreateVote, CreateHistory


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
            selectinload(self.model.category), selectinload(self.model.user), selectinload(self.model.votes),
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
                selectinload(self.model.category), selectinload(self.model.user), selectinload(self.model.votes),
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
                selectinload(self.model.category), selectinload(self.model.user), selectinload(self.model.votes),
            ).order_by(self.model.id.desc()).offset(skip).limit(limit)
        )
        return query.scalars().all()

    def get_votes(self, video: Video) -> Dict[str, int]:
        """
            Get votes
            :param video: Video
            :type video: Video
            :return: Votes
            :rtype: dict
        """
        return {
            'likes': len(list(filter(lambda vote: (vote.vote == 1), video.votes))),
            'dislikes': len(list(filter(lambda vote: (vote.vote == 0), video.votes))),
        }


class VoteCRUD(CRUD[Votes, CreateVote, CreateVote]):
    """ Vote CRUD """
    pass


class HistoryCRUD(CRUD[History, CreateHistory, CreateHistory]):
    """ History CRUD """

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
            selectinload(self.model.user), selectinload(self.model.video),
        ).order_by(self.model.id.desc()).filter_by(**kwargs))
        return query.scalars()


video_crud = VideoCRUD(Video)
vote_crud = VoteCRUD(Votes)
history_crud = HistoryCRUD(History)
