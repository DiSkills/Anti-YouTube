from datetime import datetime
from typing import List, Dict, Any

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.categories.crud import category_crud
from app.config import MEDIA_ROOT, SERVER_HOST, API_V1_URL
from app.files import write_file, remove_file
from app.service import paginate
from app.videos.crud import video_crud
from app.videos.models import Video
from app.videos.schemas import CreateVideo


async def validation(db: AsyncSession, video_file: UploadFile, preview_file: UploadFile, category_id: int) -> None:
    """
        Validation
        :param db: DB
        :type db: AsyncSession
        :param video_file: Video
        :type video_file: UploadFile
        :param preview_file: Preview
        :type preview_file: UploadFile
        :param category_id: Category ID
        :type category_id: int
        :return: None
        :raise HTTPException 400: Category not exist, video not in mp4 or preview not in jpeg/png
    """

    if not await category_crud.exists(db, id=category_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found')

    if not video_file.content_type == 'video/mp4':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Video only format in mp4')

    if preview_file.content_type not in ('image/png', 'image/jpeg'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Preview only format in jpeg or png')


async def create_video(
        db: AsyncSession, schema: CreateVideo, video_file: UploadFile, preview_file: UploadFile, user: User,
) -> Dict[str, Any]:
    """
        Create video
        :param db: DB
        :type db: AsyncSession
        :param schema: Video data
        :type schema: CreateVideo
        :param video_file: Video
        :type video_file: UploadFile
        :param preview_file: Preview
        :type preview_file: UploadFile
        :param user: User
        :type user: dict
        :return: New video
        :rtype: dict
    """

    await validation(db, video_file, preview_file, schema.category_id)

    video_name = f'{MEDIA_ROOT}{datetime.utcnow().timestamp()}.{video_file.filename.split(".")[-1]}'
    preview_name = f'{MEDIA_ROOT}{datetime.utcnow().timestamp()}.{preview_file.filename.split(".")[-1]}'

    await write_file(video_name, video_file)
    await write_file(preview_name, preview_file)
    video = await video_crud.create(db, schema, video_file=video_name, preview_file=preview_name, user_id=user.id)
    video = await video_crud.get(db, id=video.id)
    return {**video.__dict__, 'category': video.category.__dict__, 'user': video.user.__dict__}


@paginate(crud=video_crud, url=f'{SERVER_HOST}{API_V1_URL}/videos/?page=')
async def get_all_videos(*, db: AsyncSession, queryset: List[Video], page: int):
    """
        Get all videos
        :param db: DB
        :type db: AsyncSession
        :param queryset: Queryset
        :type queryset: list
        :param page: Page
        :type page: int
        :return: Videos
        :rtype: list
    """
    return [
        {
            **video.__dict__,
            'user': video.user.__dict__,
            'category': video.category.__dict__,
        } for video in queryset
    ]


async def get_video(db: AsyncSession, pk: int):
    """
        Get video
        :param db: DB
        :type db: AsyncSession
        :param pk: ID
        :type pk: int
        :return: Video
        :rtype: dict
        :raise HTTPException 400: Video not exist
    """

    if not await video_crud.exists(db, id=pk):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Video not found')

    video = await video_crud.get(db, id=pk)
    return {**video.__dict__, 'category': video.category.__dict__, 'user': video.user.__dict__}


async def delete_video(db: AsyncSession, pk: int) -> Dict[str, str]:
    """
        Delete video
        :param db: DB
        :type db: AsyncSession
        :param pk: ID
        :type pk: int
        :return: Message
        :rtype: dict
        :raise HTTPException 400: video not found
    """

    if not await video_crud.exists(db, id=pk):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Video not found')

    video = await video_crud.get(db, id=pk)

    remove_file(video.video_file)
    remove_file(video.preview_file)

    await video_crud.remove(db, id=pk)
    return {'msg': 'Video has been deleted'}
