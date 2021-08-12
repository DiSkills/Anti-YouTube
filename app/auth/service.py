from typing import Dict
from uuid import uuid4

from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import user_crud, verification_crud
from app.auth.schemas import RegisterUser, VerificationUUID, UserUpdate, LoginUser, RefreshToken
from app.auth.security import get_password_hash, verify_password
from app.auth.send_emails import send_new_account_email
from app.auth.tokens import create_token, verify_refresh_token


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
