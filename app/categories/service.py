from typing import Union, Dict, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.categories.crud import category_crud
from app.categories.schemas import CreateCategory, UpdateCategory


async def get_all_categories(db: AsyncSession) -> List[Dict[str, Union[str, int]]]:
    """
        Get all categories
        :param db: DB
        :type db: AsyncSession
        :return: Categories
        :rtype: list
    """
    return [category.__dict__ for category in await category_crud.all(db)]


async def create_category(db: AsyncSession, schema: CreateCategory) -> Dict[str, Union[str, int]]:
    """
        Create category
        :param db: DB
        :type db: AsyncSession
        :param schema: Schema
        :type schema: CreateCategory
        :return: New category
        :rtype: dict
    """
    category = await category_crud.create(db, schema)
    return category.__dict__


async def get_category(db: AsyncSession, pk: int) -> Dict[str, Union[str, int]]:
    """
        Get category
        :param db: DB
        :type db: AsyncSession
        :param pk: ID
        :type pk: int
        :return: Category
        :rtype: dict
        :raise HTTPException 400: Category not found
    """

    if not await category_crud.exists(db, id=pk):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found')

    category = await category_crud.get(db, id=pk)
    return category.__dict__


async def update_category(db: AsyncSession, pk: int, schema: UpdateCategory) -> Dict[str, Union[str, int]]:
    """
        Update category
        :param db: DB
        :type db: AsyncSession
        :param pk: ID
        :type pk: int
        :param schema: Update data
        :type schema: UpdateCategory
        :return: Updated category
        :rtype: dict
    """

    if not await category_crud.exists(db, id=pk):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found')

    category = await category_crud.update(db, pk, schema)
    return category.__dict__


async def delete_category(db: AsyncSession, pk) -> Dict[str, str]:
    """
        Delete category
        :param db: DB
        :type db: AsyncSession
        :param pk: ID
        :type pk: int
        :return: Message
        :rtype: dict
    """

    if not await category_crud.exists(db, id=pk):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found')
    await category_crud.remove(db, id=pk)
    return {'msg': 'Category has been deleted'}
