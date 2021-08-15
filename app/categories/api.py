from typing import List

from fastapi import APIRouter, status, Depends

from app.auth.permission import is_superuser
from app.categories import service
from app.categories.schemas import GetCategory, CreateCategory, UpdateCategory
from app.db import async_session
from app.schemas import Message
from app.videos.schemas import GetVideo

category_router = APIRouter()


@category_router.get(
    '/',
    response_model=List[GetCategory],
    status_code=status.HTTP_200_OK,
    description='Get all categories',
    response_description='Get all categories',
    name='Get categories',
)
async def get_all_categories():
    async with async_session() as session:
        async with session.begin():
            return await service.get_all_categories(session)


@category_router.post(
    '/',
    response_model=GetCategory,
    status_code=status.HTTP_201_CREATED,
    description='Create category',
    response_description='Create category',
    name='Create category',
    dependencies=[Depends(is_superuser)],
)
async def create_category(schema: CreateCategory):
    async with async_session() as session:
        async with session.begin():
            return await service.create_category(session, schema)


@category_router.get(
    '/{pk}',
    response_model=GetCategory,
    status_code=status.HTTP_200_OK,
    description='Get category by id',
    response_description='Get category by id',
    name='Get category',
)
async def get_category(pk: int):
    async with async_session() as session:
        async with session.begin():
            return await service.get_category(session, pk)


@category_router.put(
    '/{pk}',
    response_model=GetCategory,
    status_code=status.HTTP_200_OK,
    description='Update category by id',
    response_description='Update category by id',
    name='Update category',
    dependencies=[Depends(is_superuser)],
)
async def update_category(pk: int, schema: UpdateCategory):
    async with async_session() as session:
        async with session.begin():
            return await service.update_category(session, pk, schema)


@category_router.delete(
    '/{pk}',
    response_model=Message,
    status_code=status.HTTP_200_OK,
    description='Delete category by id',
    response_description='Delete category by id',
    name='Delete category',
    dependencies=[Depends(is_superuser)],
)
async def delete_category(pk: int):
    async with async_session() as session:
        async with session.begin():
            return await service.delete_category(session, pk)


@category_router.get(
    '/videos/{category_pk}',
    response_model=List[GetVideo],
    status_code=status.HTTP_200_OK,
    description='Get videos for category',
    response_description='Get videos for category',
    name='Get videos',
)
async def get_videos_for_category(category_pk: int):
    async with async_session() as session:
        async with session.begin():
            return await service.get_videos_for_category(session, category_pk)
