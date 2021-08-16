from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.CRUD import CRUD, ModelType
from app.comments.models import Comment
from app.comments.schemas import CreateComment


class CommentCRUD(CRUD[Comment, CreateComment, CreateComment]):
    """ Comment CRUD """

    async def get(self, db: AsyncSession, **kwargs) -> Optional[ModelType]:
        """
            Get
            :param db: DB
            :type db: AsyncSession
            :param kwargs: kwargs
            :return: Model
            :rtype: ModelType
        """
        query = await db.execute(select(self.model).options(
            selectinload(self.model.user),
        ).filter_by(**kwargs))
        return query.scalars().first()

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
            selectinload(self.model.user),
        ).order_by(self.model.id.desc()).filter_by(**kwargs))
        return query.scalars()

    async def get_children(self, db: AsyncSession, comment: Comment):
        return list(map(lambda x: x[0], await db.execute(comment.children)))


comment_crud = CommentCRUD(Comment)
