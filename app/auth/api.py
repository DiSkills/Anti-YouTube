from typing import List

from fastapi import APIRouter, status, Depends, Form, UploadFile, File, Request

from app.auth import service
from app.auth.models import User
from app.auth.permission import is_active
from app.auth.schemas import (
    RegisterUser,
    VerificationUUID,
    Tokens,
    RefreshToken,
    AccessToken,
    Password,
    ChangeUserDataResponse,
    ChangeUserData,
    Channel,
)
from app.db import async_session
from app.schemas import Message
from app.videos.schemas import GetVideo

auth_router = APIRouter()


@auth_router.post(
    '/refresh',
    status_code=status.HTTP_200_OK,
    response_model=AccessToken,
    description='Refresh token',
    response_description='Access token',
    name='Refresh token',
)
async def refresh(schema: RefreshToken):
    async with async_session() as session:
        async with session.begin():
            return await service.refresh(session, schema)


@auth_router.post(
    '/register',
    status_code=status.HTTP_201_CREATED,
    response_model=Message,
    description='Registration new user',
    response_description='User has been registration',
    name='Registration',
)
async def register(schema: RegisterUser):
    async with async_session() as session:
        async with session.begin():
            return await service.register(session, schema)


@auth_router.post(
    '/activate',
    status_code=status.HTTP_200_OK,
    response_model=Message,
    description='Activation account',
    response_description='Account activated',
    name='Activation account',
)
async def activate(schema: VerificationUUID):
    async with async_session() as session:
        async with session.begin():
            return await service.activate(session, schema)


@auth_router.post(
    '/login',
    response_model=Tokens,
    status_code=status.HTTP_200_OK,
    description='Login',
    response_description='Tokens',
    name='Login',
)
async def login(username: str = Form(...), password: str = Form(...)):
    async with async_session() as session:
        async with session.begin():
            return await service.login(session, username, password)


@auth_router.post(
    '/follow',
    response_model=Message,
    status_code=status.HTTP_200_OK,
    description='Follow',
    response_description='Follow',
    name='Follow',
)
async def follow(to_id: int, user: User = Depends(is_active)):
    async with async_session() as session:
        async with session.begin():
            return await service.follow(session, to_id, user)


@auth_router.post(
    '/unfollow',
    response_model=Message,
    status_code=status.HTTP_200_OK,
    description='Unfollow',
    response_description='Unfollow',
    name='Unfollow',
)
async def unfollow(to_id: int, user: User = Depends(is_active)):
    async with async_session() as session:
        async with session.begin():
            return await service.unfollow(session, to_id, user)


@auth_router.get(
    '/request-password-reset',
    response_model=Message,
    status_code=status.HTTP_200_OK,
    description='Request reset password',
    response_description='Request reset password',
    name='Request reset password',
)
async def create_reset_password(email: str):
    async with async_session() as session:
        async with session.begin():
            return await service.create_reset_password(session, email)


@auth_router.post(
    '/password-reset',
    response_model=Message,
    status_code=status.HTTP_200_OK,
    description='Reset password',
    response_description='Reset password',
    name='Reset password',
)
async def verify_password_reset(token: str, schema: Password):
    async with async_session() as session:
        async with session.begin():
            return await service.verify_password_reset(session, token, schema)


@auth_router.post(
    '/username',
    response_model=Message,
    status_code=status.HTTP_200_OK,
    description='Get username from email',
    response_description='Get username from email',
    name='Get username',
)
async def get_username(email: str):
    async with async_session() as session:
        async with session.begin():
            return await service.get_username(session, email)


@auth_router.get(
    '/change-data',
    response_model=ChangeUserDataResponse,
    status_code=status.HTTP_200_OK,
    description='Get user data',
    response_description='Get user data',
    name='Get user data',
)
async def get_data(user: User = Depends(is_active)):
    return await service.get_data(user)


@auth_router.put(
    '/change-data',
    response_model=ChangeUserDataResponse,
    status_code=status.HTTP_200_OK,
    description='Change user data',
    response_description='Change user data',
    name='Change user data',
)
async def change_data(schema: ChangeUserData, user: User = Depends(is_active)):
    async with async_session() as session:
        async with session.begin():
            return await service.change_data(session, schema, user)


@auth_router.post(
    '/avatar',
    response_model=ChangeUserDataResponse,
    status_code=status.HTTP_200_OK,
    description='Upload avatar',
    response_description='Upload avatar',
    name='Upload avatar',
)
async def upload_avatar(avatar: UploadFile = File(...), user: User = Depends(is_active)):
    async with async_session() as session:
        async with session.begin():
            return await service.upload_avatar(session, avatar, user)


@auth_router.get(
    '/history',
    response_model=List[GetVideo],
    status_code=status.HTTP_200_OK,
    description='Get history',
    response_description='Get history',
    name='History',
)
async def get_history(user: User = Depends(is_active)):
    async with async_session() as session:
        async with session.begin():
            return await service.get_history(session, user)


@auth_router.get(
    '/channel',
    response_model=Channel,
    status_code=status.HTTP_200_OK,
    description='Get channel',
    response_description='Get channel',
    name='Get channel',
)
async def get_channel(pk: int, request: Request):
    async with async_session() as session:
        async with session.begin():
            return await service.get_channel(session, pk, request)
