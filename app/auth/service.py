from typing import Dict
from uuid import uuid4

from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import user_crud, verification_crud
from app.auth.schemas import RegisterUser, VerificationUUID, UserUpdate
from app.auth.security import get_password_hash
from app.auth.send_emails import send_new_account_email


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

    user = user.__dict__

    verification = await verification_crud.create(db, VerificationUUID(uuid=str(uuid4())), user_id=user['id'])

    send_new_account_email(user['email'], user['username'], schema.password, verification.__dict__['uuid'])

    return {'msg': 'Send email for activate account'}


async def activate(db: AsyncSession, schema: VerificationUUID):
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

    verification = verification.__dict__

    await user_crud.update(db, verification['user_id'], UserUpdate(is_active=True))

    await verification_crud.remove(db, id=verification['id'])

    return {'msg': 'Account has been is activated'}
