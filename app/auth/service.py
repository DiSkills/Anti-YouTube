from datetime import datetime
from typing import Dict, Any, List, Union
from uuid import uuid4

from fastapi import status, HTTPException, UploadFile, Request
from pyotp import TOTP, random_base32
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import user_crud, verification_crud
from app.auth.models import User
from app.auth.permission import is_auth_or_anonymous
from app.auth.schemas import (
    RegisterUser,
    VerificationUUID,
    UserUpdate,
    LoginUser,
    RefreshToken,
    Password,
    ChangeUserData,
    UploadAvatar,
    ChangePassword,
    Change2StepAuth,
)
from app.auth.security import get_password_hash, verify_password
from app.auth.send_emails import send_new_account_email, send_reset_password_email, send_username_email, \
    send_about_change_password
from app.auth.tokens import create_token, verify_refresh_token, create_password_reset_token, verify_password_reset_token
from app.config import MEDIA_ROOT
from app.files import remove_file, write_file
from app.videos.crud import history_crud, video_crud


async def refresh(db: AsyncSession, schema: RefreshToken):
    """
        Refresh token
        :param db: DB
        :type db: AsyncSession
        :param schema: Refresh token
        :type schema: RefreshToken
        :return: Access token
        :rtype: dict
        :raise HTTPException 400: User not found
    """

    username = verify_refresh_token(schema.refresh_token)

    if not await user_crud.exists(db, username=username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')

    user = await user_crud.get(db, username=username)
    return create_token(user.id, username)


async def register(db: AsyncSession, schema: RegisterUser) -> Dict[str, str]:
    """
        Register
        :param db: DB
        :type db: AsyncSession
        :param schema: Register data
        :type schema: RegisterUser
        :return: Message
        :rtype: dict
        :raise HTTPException 400: Username or email exist
    """

    if await user_crud.exists(db, username=schema.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Username exist')

    if await user_crud.exists(db, email=schema.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email exist')

    del schema.confirm_password

    user = await user_crud.create(db, schema, password=get_password_hash(schema.password))

    verification = await verification_crud.create(db, VerificationUUID(uuid=str(uuid4())), user_id=user.id)

    send_new_account_email(user.email, user.username, schema.password, verification.uuid)

    return {'msg': 'Send email for activate account'}


async def activate(db: AsyncSession, schema: VerificationUUID) -> Dict[str, str]:
    """
        Activation account
        :param db: DB
        :type db: AsyncSession
        :param schema: UUID
        :type schema: VerificationUUID
        :return: Message
        :rtype: dict
        :raise HTTPException 400: Verification not exist
    """

    if not await verification_crud.exists(db, uuid=schema.uuid):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Verification not found')

    verification = await verification_crud.get(db, uuid=schema.uuid)

    await user_crud.update(db, verification.user_id, UserUpdate(is_active=True))

    await verification_crud.remove(db, id=verification.id)

    return {'msg': 'Account has been is activated'}


async def validation_login(db: AsyncSession, username: str, password: str) -> User:
    """
        Validation login data
        :param db: DB
        :type db: AsyncSession
        :param username: Username
        :type username: str
        :param password: Password
        :type password: str
        :return: User
        :rtype: User
        :raise HTTPException 400: User not exist or password mismatch or user not activated
    """
    schema = LoginUser(username=username, password=password)

    if not await user_crud.exists(db, username=schema.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')

    user = await user_crud.get(db, username=schema.username)

    if not verify_password(schema.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Password mismatch')

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You not activated')
    return user


async def login(db: AsyncSession, username: str, password: str) -> Dict[str, Union[str, int]]:
    """
        Login
        :param db: DB
        :type db: AsyncSession
        :param username: Username
        :type username: str
        :param password: Password
        :type password: str
        :return: Tokens
        :rtype: dict
        :raise HTTPException 403: User has 2-step auth
    """

    user = await validation_login(db, username, password)

    if user.two_auth:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You have 2-step auth')

    return {**create_token(user.id, user.username), 'user_id': user.id, 'is_superuser': user.is_superuser}


async def two_auth(db: AsyncSession, username: str, password: str, code: str) -> Dict[str, Union[str, int]]:
    """
        2-step auth
        :param db: DB
        :type db: AsyncSession
        :param username: Username
        :type username: str
        :param password: Password
        :type password: str
        :param code: Auth code
        :type code: str
        :return: Tokens
        :rtype: dict
    """

    user = await validation_login(db, username, password)
    if not user.two_auth:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You don\'t have 2-step auth')
    totp = TOTP(user.otp_secret)
    if not totp.verify(code):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Bad code')
    return {**create_token(user.id, user.username), 'user_id': user.id}


async def follow(db: AsyncSession, to_id: int, user: User) -> Dict[str, str]:
    """
        Follow
        :param db: DB
        :type db: AsyncSession
        :param to_id: To user ID
        :type to_id: int
        :param user: User
        :type user: User
        :return: Message
        :rtype: dict
        :raise HTTPException 400: Follow to user not found or You are already followed or You not follow to self
    """

    if to_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You not follow to self')

    if not await user_crud.exists(db, id=to_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Follow to user not found')

    to_user = await user_crud.get(db, id=to_id)

    user = await user_crud.get(db, id=user.id)

    await user.follow(db, to_user)
    return {'msg': 'You follow to user'}


async def unfollow(db: AsyncSession, to_id: int, user: User) -> Dict[str, str]:
    """
        Unfollow
        :param db: DB
        :type db: AsyncSession
        :param to_id: To user ID
        :type to_id: int
        :param user: User
        :type user: User
        :return: Message
        :rtype: dict
        :raise HTTPException 400: unfollow to user not found or You are already unfollowed or You not unfollow to self
    """

    if to_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You not unfollow to self')

    if not await user_crud.exists(db, id=to_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Unfollow to user not found')

    to_user = await user_crud.get(db, id=to_id)

    user = await user_crud.get(db, id=user.id)

    await user.unfollow(db, to_user)
    return {'msg': 'You unfollow to user'}


async def create_reset_password(db: AsyncSession, email: str) -> Dict[str, str]:
    """
        Create password reset
        :param db: DB
        :type db: AsyncSession
        :param email: Email
        :type email: str
        :return: Message
        :rtype: dict
        :raise HTTPException 400: User not exist
    """

    if not await user_crud.exists(db, email=email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')

    token = create_password_reset_token(email)
    user = await user_crud.get(db, email=email)
    send_reset_password_email(user.email, user.username, user.password, token)
    return {'msg': 'Email send'}


async def verify_password_reset(db: AsyncSession, token: str, schema: Password) -> Dict[str, str]:
    """
        Verify and reset password
        :param db: DB
        :type db: AsyncSession
        :param token: Token
        :type token: str
        :param schema: New password
        :type schema: Password
        :return: Message
        :rtype: dict
        :raise HTTPException 400: User not exist
    """

    email = verify_password_reset_token(token)

    if not await user_crud.exists(db, email=email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')

    user = await user_crud.get(db, email=email)

    del schema.confirm_password

    await user_crud.update(
        db, user.id, schema, password=get_password_hash(schema.password), two_auth=False, otp_secret=random_base32(),
    )
    return {'msg': 'Password has been reset'}


async def get_username(db: AsyncSession, email: str) -> Dict[str, str]:
    """
        Get username for email
        :param db: DB
        :type db: AsyncSession
        :param email: Email
        :type email: str
        :return: Message
        :rtype: dict
        :raise HTTPException 400: User not exist
    """

    if not await user_crud.exists(db, email=email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')

    user = await user_crud.get(db, email=email)
    send_username_email(user.email, user.username)
    return {'msg': 'Email send'}


async def get_data(user: User) -> Dict[str, Any]:
    """
        Get user data
        :param user: User
        :type user: User
        :return: User
        :rtype: dict
    """
    return user.__dict__


async def change_data(db: AsyncSession, schema: ChangeUserData, user: User) -> Dict[str, Any]:
    """
        Change user data
        :param db: DB
        :type db: AsyncSession
        :param schema: New user data
        :type schema: ChangeUserData
        :param user: User
        :type user: User
        :return: User with new data
        :rtype: dict
    """
    user = await user_crud.update(db, user.id, schema)
    return user.__dict__


async def upload_avatar(db: AsyncSession, avatar: UploadFile, user: User) -> Dict[str, Any]:
    """
        Upload avatar
        :param db: DB
        :type db: AsyncSession
        :param avatar: Avatar
        :type avatar: UploadFile
        :param user: User
        :type user: User
        :return: User
        :rtype: dict
        :raise HTTPException 400: Video format not png or jpeg
    """

    if avatar.content_type not in ('image/png', 'image/jpeg'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Avatar only format in jpeg or png')

    if MEDIA_ROOT in user.avatar:
        remove_file(user.avatar)

    avatar_name = f'{MEDIA_ROOT}{datetime.utcnow().timestamp()}.{avatar.filename.split(".")[-1]}'

    await write_file(avatar_name, avatar)

    user = await user_crud.update(db, user.id, UploadAvatar(avatar=avatar_name))
    return user.__dict__


async def get_history(db: AsyncSession, user: User) -> List[Dict[str, Any]]:
    """
        Get history
        :param db: DB
        :type db: AsyncSession
        :param user: User
        :type user: User
        :return: History
        :rtype: list
    """
    history = []
    for history_video in await history_crud.filter(db, user_id=user.id):
        video = await video_crud.get(db, id=history_video.video.id)
        to_history = {
            **history_video.video.__dict__,
            'category': video.category.__dict__,
            'votes': video_crud.get_votes(history_video.video),
            'user': video.user.__dict__
        }
        history.append(to_history)

    return history


async def get_channel(db: AsyncSession, pk, request: Request) -> Dict[str, Any]:
    """
        Channel
        :param db: DB
        :type db: AsyncSession
        :param pk: User ID
        :type pk: int
        :param request: Request
        :type request: Request
        :return: Channel
        :rtype: dict
        :raise HTTPException 400: User not found
    """

    if not await user_crud.exists(db, id=pk):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')

    is_following = None

    user = await is_auth_or_anonymous(request)
    channel = await user_crud.get(db, id=pk)
    if user:
        user = await user_crud.get(db, id=user.id)
        if user.id != pk:
            is_following = await user.is_following(db, channel)
        else:
            is_following = 3
    views, count_videos = await video_crud.count_views_and_videos(db, user_id=pk)
    return {
        **channel.__dict__,
        'followers_count': await user_crud.count_followers(db, pk),
        'is_following': is_following,
        'views': views or 0,
        'count_videos': count_videos,
    }


async def get_channel_videos(db: AsyncSession, pk: int) -> List[Dict[str, Any]]:
    """
        Get channel videos
        :param db: DB
        :type db: AsyncSession
        :param pk: Channel ID
        :type pk: int
        :return: Videos
        :rtype: list
        :raise HTTPException 400: User not found
    """

    if not await user_crud.exists(db, id=pk):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')

    videos = await video_crud.filter(db, user_id=pk)
    return [
        {
            **video.__dict__,
            'user': video.user.__dict__,
            'votes': video_crud.get_votes(video),
            'category': video.category.__dict__,
        } for video in videos
    ]


async def subscriptions(db: AsyncSession, user: User) -> List[Dict[str, Any]]:
    """
        Subscriptions
        :param db: DB
        :type db: AsyncSession
        :param user: User
        :type user: User
        :return: Subscriptions
        :rtype: list
    """
    user = await user_crud.get(db, id=user.id)
    subscriptions_list = await user_crud.get_subscriptions(db, user)
    followed_list = []
    for subscription in subscriptions_list:
        followed = {
            'user': subscription.__dict__,
            'videos': [
                {
                    **video.__dict__,
                    'user': video.user.__dict__,
                    'votes': video_crud.get_votes(video),
                    'category': video.category.__dict__,
                } for video in await video_crud.filter(db, user_id=subscription.id)
            ],
        }
        followed_list.append(followed)
    return followed_list


async def change_password(db: AsyncSession, schema: ChangePassword, user: User) -> Dict[str, str]:
    """
        Change password
        :param db: DB
        :type db: AsyncSession
        :param schema: Change data
        :type schema: ChangePassword
        :param user: User
        :type user: User
        :return: Message
        :rtype: dict
    """

    if not verify_password(schema.old_password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Old password mismatch')

    del schema.old_password
    del schema.confirm_password
    await user_crud.update(db, user.id, schema, password=get_password_hash(schema.password))
    send_about_change_password(user.email, user.username, schema.password)
    return {'msg': 'Password has been changed'}


async def toggle_2step_auth(db: AsyncSession, user: User) -> Dict[str, str]:
    """
        Toggle 2-step auth
        :param db: DB
        :type db: AsyncSession
        :param user: User
        :type user: User
        :return: Message or QR url
        :rtype: dict
    """
    if user.two_auth:
        await user_crud.update(db, user.id, Change2StepAuth(two_auth=False))
        return {'msg': 'You off 2-step auth'}
    qr_url = TOTP(user.otp_secret).provisioning_uri(name=user.username, issuer_name='Anti-YouTube')
    await user_crud.update(db, user.id, Change2StepAuth(two_auth=True))
    return {'msg': qr_url}
