from typing import List

from celery.result import AsyncResult
from fastapi import APIRouter, status, Depends, Form, UploadFile, File, Request, WebSocket
from fastapi.responses import RedirectResponse

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
    ChangePassword,
    Tasks,
)
from app.config import oauth
from app.db import async_session
from app.schemas import Message
from app.videos.schemas import GetVideo, SubscriptionsVideos

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


@auth_router.get(
    '/channel/videos/{pk}',
    response_model=List[GetVideo],
    status_code=status.HTTP_200_OK,
    description='Get channel videos',
    response_description='Get channel videos',
    name='Get channel videos',
)
async def get_channel_videos(pk: int):
    async with async_session() as session:
        async with session.begin():
            return await service.get_channel_videos(session, pk)


@auth_router.get(
    '/followed',
    response_model=List[SubscriptionsVideos],
    status_code=status.HTTP_200_OK,
    description='Subscriptions',
    response_description='Subscriptions',
    name='Subscriptions',
)
async def subscriptions(user: User = Depends(is_active)):
    async with async_session() as session:
        async with session.begin():
            return await service.subscriptions(session, user)


@auth_router.put(
    '/change-password',
    response_model=Message,
    status_code=status.HTTP_200_OK,
    description='Change password',
    response_description='Change password',
    name='Change password',
)
async def change_password(schema: ChangePassword, user: User = Depends(is_active)):
    async with async_session() as session:
        async with session.begin():
            return await service.change_password(session, schema, user)


@auth_router.post(
    '/2-auth',
    response_model=Tokens,
    status_code=status.HTTP_200_OK,
    description='2-step login',
    response_description='2-step login',
    name='2-step login',
)
async def two_auth(username: str = Form(...), password: str = Form(...), code: str = Form(...)):
    async with async_session() as session:
        async with session.begin():
            return await service.two_auth(session, username, password, code)


@auth_router.get(
    '/2-auth-toggle',
    response_model=Message,
    status_code=status.HTTP_200_OK,
    description='On/off 2-step',
    response_description='On/off 2-step',
    name='On/off 2-step',
)
async def toggle_2step_auth(user: User = Depends(is_active)):
    async with async_session() as session:
        async with session.begin():
            return await service.toggle_2step_auth(session, user)


@auth_router.get(
    '/google-login',
    description='Google login',
    response_description='Google login',
    name='Google login',
)
async def google_login(request: Request):
    redirect_uri = 'http://localhost:8000/api/v1/auth/google-auth'
    return await oauth.google.authorize_redirect(request, redirect_uri)


@auth_router.get(
    '/google-auth',
    response_class=RedirectResponse,
    description='Google auth',
    response_description='Google auth',
    name='Google auth',
)
async def google_auth(request: Request):
    async with async_session() as session:
        async with session.begin():
            token = await oauth.google.authorize_access_token(request)
            user = await oauth.google.parse_id_token(request, token)
            return await service.google_auth(session, user)


@auth_router.post(
    '/export',
    response_model=Tasks,
)
async def export(user: User = Depends(is_active)):
    async with async_session() as session:
        async with session.begin():
            return await service.export(session, user)


@auth_router.websocket('/task-status')
async def task_status(websocket: WebSocket):
    await websocket.accept()

    while True:
        task_id = await websocket.receive_text()
        task = AsyncResult(task_id)
        if task.status == 'PENDING':
            response = {
                'state': task.state,
                'progress': 0,
            }
            await websocket.send_json(response)
        else:
            response = {
                'state': task.state,
                'progress': task.info.get('progress', 0),
            }
            await websocket.send_json(response)
            if task.info.get('progress') == 100:
                break
