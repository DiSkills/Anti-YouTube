from fastapi import APIRouter, status, Form, UploadFile, File, Depends, Query

from app.auth.models import User
from app.auth.permission import is_active, is_superuser
from app.db import async_session
from app.schemas import Message
from app.videos import service
from app.videos.schemas import GetVideo, CreateVideo, VideoPaginate

videos_router = APIRouter()


@videos_router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    response_model=GetVideo,
    description='Create video',
    response_description='Create video',
    name='Create video',
)
async def create_video(
        title: str = Form(...),
        description: str = Form(...),
        category_id: int = Form(...),
        video_file: UploadFile = File(...),
        preview_file: UploadFile = File(...),
        user: User = Depends(is_active)
):
    async with async_session() as session:
        async with session.begin():
            schema: CreateVideo = CreateVideo(title=title, description=description, category_id=category_id)
            return await service.create_video(session, schema, video_file, preview_file, user)


@videos_router.get(
    '/',
    status_code=status.HTTP_200_OK,
    response_model=VideoPaginate,
    description='Get all videos',
    response_description='Get all videos',
    name='Get videos',
)
async def get_all_videos(page: int = Query(1, gt=0)):
    async with async_session() as session:
        async with session.begin():
            return await service.get_all_videos(db=session, page=page)


@videos_router.get(
    '/{pk}',
    status_code=status.HTTP_200_OK,
    response_model=GetVideo,
    description='Get video',
    response_description='Get video',
    name='Get video',
)
async def get_video(pk: int):
    async with async_session() as session:
        async with session.begin():
            return await service.get_video(session, pk)


@videos_router.delete(
    '/{pk}',
    status_code=status.HTTP_200_OK,
    response_model=Message,
    description='Delete video',
    response_description='Delete video',
    name='Delete video',
    dependencies=[Depends(is_superuser)],
)
async def delete_video(pk: int):
    async with async_session() as session:
        async with session.begin():
            return await service.delete_video(session, pk)
