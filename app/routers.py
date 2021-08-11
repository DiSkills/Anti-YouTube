from fastapi import APIRouter

from app.auth.api import auth_router

routers = APIRouter()

routers.include_router(auth_router, prefix='/auth', tags=['auth'])
