from fastapi import APIRouter, status, Depends

from app.auth.models import User
from app.auth.permission import is_active
from app.comments import service
from app.comments.schemas import CreateComment
from app.db import async_session

comments_router = APIRouter()


@comments_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_comment(schema: CreateComment, user: User = Depends(is_active)):
    async with async_session() as session:
        async with session.begin():
            return await service.create_comment(session, schema, user)
