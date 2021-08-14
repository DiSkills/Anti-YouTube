from fastapi import APIRouter, status, Form, UploadFile, File, Depends

from app.auth.models import User
from app.auth.permission import is_active
from app.db import async_session
from app.videos import service
from app.videos.schemas import GetVideo, CreateVideo

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
