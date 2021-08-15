from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Generator, IO

from fastapi import UploadFile, HTTPException, status, Request
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


def ranged(
        file: IO[bytes],
        start: int = 0,
        end: int = None,
        block_size: int = 8192,
) -> Generator[bytes, None, None]:
    """
        Ranged video
        :param file: video
        :type file: IO
        :param start: start
        :type start: int
        :param end: end
        :type end: int
        :param block_size: Block size
        :type block_size: int
        :return: Generator
        :rtype: Generator
    """

    consumed = 0

    file.seek(start)
    while True:
        data_length = min(block_size, end - start - consumed) if end else block_size
        if data_length <= 0:
            break
        data = file.read(data_length)
        if not data:
            break
        consumed += data_length
        yield data

    if hasattr(file, 'close'):
        file.close()


async def open_file(db: AsyncSession, request: Request, pk: int) -> tuple:
    """
        Open file
        :param db: DB
        :type db: AsyncSession
        :param request: Request
        :type request: Request
        :param pk: ID
        :type pk: int
        :return: Tuple
        :rtype: tuple
        :raise HTTPException 400: Video not found
    """

    if not await video_crud.exists(db, id=pk):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Video not found')

    video_file = await video_crud.get(db, id=pk)
    path = Path(video_file.video_file)
    file = path.open('rb')
    file_size = path.stat().st_size

    content_length = file_size
    status_code = status.HTTP_200_OK
    headers = {}
    content_range = request.headers.get('range')

    if content_range is not None:
        content_range = content_range.strip().lower()
        content_ranges = content_range.split('=')[-1]
        range_start, range_end, *_ = map(str.strip, (content_ranges + '-').split('-'))
        range_start = max(0, int(range_start)) if range_start else 0
        range_end = min(file_size - 1, int(range_end)) if range_end else file_size - 1
        content_length = (range_end - range_start) + 1
        file = ranged(file, start=range_start, end=range_end + 1)
        status_code = status.HTTP_206_PARTIAL_CONTENT
        headers['Content-Range'] = f'bytes {range_start}-{range_end}/{file_size}'

    return file, status_code, content_length, headers
