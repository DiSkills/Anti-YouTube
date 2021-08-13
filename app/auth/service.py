from typing import Dict
from uuid import uuid4

from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import user_crud, verification_crud
from app.auth.models import User
from app.auth.schemas import RegisterUser, VerificationUUID, UserUpdate, LoginUser, RefreshToken, Password
from app.auth.security import get_password_hash, verify_password
from app.auth.send_emails import send_new_account_email, send_reset_password_email, send_username_email
from app.auth.tokens import create_token, verify_refresh_token, create_password_reset_token, verify_password_reset_token


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


async def login(db: AsyncSession, schema: LoginUser) -> Dict[str, str]:
    """
        Login
        :param db: DB
        :type db: AsyncSession
        :param schema: Login data
        :type schema: LoginUser
        :return: Tokens
        :rtype: dict
        :raise HTTPException 400: User not exist or password mismatch
    """

    if not await user_crud.exists(db, username=schema.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')

    user = await user_crud.get(db, username=schema.username)

    if not verify_password(schema.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Password mismatch')

    return create_token(user.id, user.username)


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

    await user_crud.update(db, user.id, schema, password=get_password_hash(schema.password))
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
