from fastapi import APIRouter, status, Depends

from app.auth import service
from app.auth.models import User
from app.auth.permission import is_active
from app.auth.schemas import RegisterUser, VerificationUUID, LoginUser, Tokens, RefreshToken, AccessToken, Password
from app.db import async_session
from app.schemas import Message

auth_router = APIRouter()


@auth_router.post('/refresh', status_code=status.HTTP_200_OK, response_model=AccessToken)
async def refresh(schema: RefreshToken):
    async with async_session() as session:
        async with session.begin():
            return await service.refresh(session, schema)


@auth_router.post('/register', status_code=status.HTTP_201_CREATED, response_model=Message)
async def register(schema: RegisterUser):
    async with async_session() as session:
        async with session.begin():
            return await service.register(session, schema)


@auth_router.post('/activate', status_code=status.HTTP_200_OK, response_model=Message)
async def activate(schema: VerificationUUID):
    async with async_session() as session:
        async with session.begin():
            return await service.activate(session, schema)


@auth_router.post('/login', response_model=Tokens, status_code=status.HTTP_200_OK)
async def login(schema: LoginUser):
    async with async_session() as session:
        async with session.begin():
            return await service.login(session, schema)


@auth_router.post('/follow', response_model=Message, status_code=status.HTTP_200_OK)
async def follow(to_id: int, user: User = Depends(is_active)):
    async with async_session() as session:
        async with session.begin():
            return await service.follow(session, to_id, user)


@auth_router.post('/unfollow', response_model=Message, status_code=status.HTTP_200_OK)
async def unfollow(to_id: int, user: User = Depends(is_active)):
    async with async_session() as session:
        async with session.begin():
            return await service.unfollow(session, to_id, user)


@auth_router.get('/request-password-reset', response_model=Message, status_code=status.HTTP_200_OK)
async def create_reset_password(email: str):
    async with async_session() as session:
        async with session.begin():
            return await service.create_reset_password(session, email)


@auth_router.post('/password-reset', response_model=Message, status_code=status.HTTP_200_OK)
async def verify_password_reset(token: str, schema: Password):
    async with async_session() as session:
        async with session.begin():
            return await service.verify_password_reset(session, token, schema)
