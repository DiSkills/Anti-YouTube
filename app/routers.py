from fastapi import APIRouter
from fastapi.responses import FileResponse

from app import service
from app.auth.api import auth_router
from app.categories.api import category_router
from app.comments.api import comments_router
from app.videos.api import videos_router

routers = APIRouter()


@routers.get(
    '/media/{file_name}',
    tags=['media'],
    response_class=FileResponse,
    description='Get media',
    response_description='Get media',
    name='Media',
)
async def get_file(file_name: str) -> FileResponse:
    """
        Get media file
        :param file_name: File name
        :type file_name: str
        :return: File
        :rtype: FileResponse
    """
    return await service.get_file(file_name)

routers.include_router(auth_router, prefix='/auth', tags=['auth'])
routers.include_router(category_router, prefix='/categories', tags=['categories'])
routers.include_router(videos_router, prefix='/videos', tags=['videos'])
routers.include_router(comments_router, prefix='/comments', tags=['comments'])
