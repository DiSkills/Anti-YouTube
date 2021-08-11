from typing import List, Optional, Generic, TypeVar, Type

import sqlalchemy
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar('ModelType', bound=sqlalchemy.Table)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)


class CRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """ Base CRUD """

    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

    async def get(self, db: AsyncSession,  **kwargs) -> Optional[ModelType]:
        """
            Get
            :param db: DB
            :type db: AsyncSession
            :param kwargs: kwargs
            :return: Model
            :rtype: ModelType
        """
        query = await db.execute(select(self.model).filter_by(**kwargs))
        return query.first()

    async def exists(self,  db: AsyncSession, **kwargs):
        """
            Exists
            :param db: DB
            :type db: AsyncSession
            :param kwargs: kwargs
            :return: Exists?
        """
        query = await db.execute(select(self.model).filter_by(**kwargs).exists())
        return query.scalar()

    async def page_exists(self, db: AsyncSession, skip: int, limit: int):
        """
            Next query exists?
            :param db: DB
            :type db: AsyncSession
            :param skip: Skip
            :type skip: int
            :param limit: Limit
            :type limit: int
            :return: Page exists?
        """
        return await db.execute(select(self.model).order_by(self.model.id.desc()).offset(skip).limit(limit))

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
        query = await db.execute(select(self.model).order_by(self.model.id.desc()).offset(skip).limit(limit))
        return query.scalars().all()

    async def create(self, db: AsyncSession,  schema: CreateSchemaType, **kwargs) -> ModelType:
        """
            Create
            :param db: DB
            :type db: AsyncSession
            :param schema: data
            :type schema: CreateSchemaType
            :param kwargs: kwargs
            :return: New model
            :rtype: ModelType
        """
        data = jsonable_encoder(schema)
        obj = self.model(**{**data, **kwargs})
        db.add(obj)
        await db.flush()
        return obj

    async def remove(self, db: AsyncSession, **kwargs) -> None:
        """
            Remove
            :param db: DB
            :type db: AsyncSession
            :param kwargs: kwargs
            :return: None
        """
        return await db.execute(delete(self.model).filter_by(**kwargs))

    async def update(self, db: AsyncSession,  pk: int, schema: UpdateSchemaType, **kwargs) -> ModelType:
        """
            Update
            :param db: DB
            :type db: AsyncSession
            :param pk: ID
            :type pk: int
            :param schema: Update data
            :type schema: UpdateSchemaType
            :param kwargs: kwargs
            :return: Updated model
            :rtype: ModelType
        """
        update_data = {**schema.dict(skip_defaults=True), **kwargs}
        query = update(self.model).filter(self.model.id == pk).values(**update_data)
        query.execution_options(synchronize_session="fetch")
        return await db.execute(query)
