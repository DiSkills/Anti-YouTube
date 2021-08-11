from datetime import datetime, timedelta

import jwt

from fastapi import HTTPException, status

from typing import Dict, Optional

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, REFRESH_TOKEN_EXPIRE_MINUTES

ALGORITHM = 'HS256'
access_token_jwt_subject = 'access'


def create_jwt_token(data: Dict, expires_delta: timedelta = None) -> str:
    """
        Create access token
        :param data: Data
        :type data: Dict[str, int]
        :param expires_delta: Lifetime
        :type expires_delta: timedelta
        :return: Token
        :rtype: str
    """

    encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=15)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    encode.update({'exp': expire, 'sub': access_token_jwt_subject})
    encoded_jwt = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_token(user_id: int, username: str) -> Dict[str, str]:
    """
        Create token
        :param user_id: User id
        :param username: Username
        :type user_id: int
        :type username: str
        :return: Token
        :rtype: Dict[str, str]
    """

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    return {
        'access_token': create_jwt_token({'user_id': user_id}, access_token_expires),
        'refresh_token': create_jwt_token({'username': username}, refresh_token_expires),
        'token_type': 'bearer',
    }


def create_password_reset_token(email: str) -> str:
    """
        Create password reset token
        :param email: Email
        :type email: str
        :return: Token
        :rtype: str
    """
    access_token_expires = timedelta(minutes=10)
    return create_jwt_token({'email': email}, access_token_expires)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
        Verify password reset token
        :param token: Token
        :type token: str
        :return: Email or None
        :rtype: str
        :raise HTTPException 400: Reset token not found
        :raise HTTPException 401: Token lifetime ended
    """
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        if 'email' not in decoded.keys():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Reset token not found')
        return decoded['email']
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token lifetime ended')


def verify_refresh_token(token: str) -> Optional[str]:
    """
        Verify refresh token
        :param token: Refresh token
        :type token: str
        :return: Username or None
        :rtype: str
        :raise HTTPException 400: Refresh token not found
        :raise HTTPException 401: Token lifetime ended
    """
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        if 'username' not in decoded.keys():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Refresh token not found')
        return decoded['username']
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token lifetime ended')
