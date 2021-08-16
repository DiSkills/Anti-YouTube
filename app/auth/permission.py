from typing import Optional

import jwt
from fastapi import Security, HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordBearer

from app.auth.crud import user_crud
from app.auth.models import User
from app.auth.schemas import TokenPayload
from app.auth.tokens import ALGORITHM
from app.config import SECRET_KEY
from app.db import async_session

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')


async def is_authenticated(token: str = Security(reusable_oauth2)) -> User:
    """
        Is authenticated only
        :param token: Token
        :type token: str
        :return: User
        :rtype: User
        :raise HTTPException 400: Not access token
        :raise HTTPException 401: Token lifetime ended
        :raise HTTPException 403: JWT Token error
        :raise HTTPException 404: Not user
    """

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if 'user_id' not in payload.keys():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Access token not found')
        token_data = TokenPayload(**payload)
    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token lifetime ended')
    except jwt.exceptions.PyJWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Could not validate credentials')

    async with async_session() as session:
        async with session.begin():
            if not await user_crud.exists(session, id=token_data.user_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

            return await user_crud.get(session, id=token_data.user_id)


async def is_active(user: User = Depends(is_authenticated)) -> User:
    """
        User is active
        :param user: User
        :type user: dict
        :return: User
        :rtype: User
        :raise HTTPException 403: User not active
    """

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='User not active')
    return user


async def is_superuser(user: User = Depends(is_active)) -> User:
    """
        User is superuser
        :param user: User
        :type user: dict
        :return: User
        :rtype: User
        :raise HTTPException 403: User not superuser
    """

    if not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='User not superuser')
    return user


async def is_auth_or_anonymous(request: Request) -> Optional[User]:
    """
        If user return user else None
        :param request: Request
        :type request: Request
        :return: User or None
        :rtype: dict
    """
    if 'authorization' in request.headers.keys():
        try:
            return await is_active(await is_authenticated(request.headers.get('authorization').split(' ')[-1]))
        except:
            return
