from fastapi import APIRouter, status, Depends

from app.auth.models import User
from app.auth.permission import is_active
from app.comments import service
from app.comments.schemas import CreateComment, GetComment
from app.db import async_session

comments_router = APIRouter()


@comments_router.get(
    '/video/{pk}',
    # response_model=List[GetAllComments],
    status_code=status.HTTP_200_OK,
    description='Get comments for video',
    response_description='Get comments for video',
    name='Comments',
)
async def get_comments(pk: int):
    async with async_session() as session:
        async with session.begin():
            return await service.get_comments(session, pk)


@comments_router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    response_model=GetComment,
    description='Create comment',
    response_description='Create comment',
    name='Create comment',
)
async def create_comment(schema: CreateComment, user: User = Depends(is_active)):
    async with async_session() as session:
        async with session.begin():
            return await service.create_comment(session, schema, user)
