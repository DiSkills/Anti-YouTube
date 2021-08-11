from fastapi import APIRouter, status

from app.auth import service
from app.auth.schemas import RegisterUser, VerificationUUID, LoginUser, Tokens
from app.db import async_session
from app.schemas import Message

auth_router = APIRouter()


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
