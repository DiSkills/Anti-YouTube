import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import TESTS, API_V1_URL, MEDIA_ROOT, DOCKER
from app.db import engine, Base
from scripts.createsuperuser import createsuperuser_docker

app = FastAPI(
    title='FastAPI Anti-YouTube',
    description='FastAPI Anti-YouTube by _Counter021_',
    version='0.3.3',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def startup():
    async with engine.begin() as conn:
        if not TESTS:
            await conn.run_sync(Base.metadata.create_all)

    if int(DOCKER):
        await createsuperuser_docker()

    if not os.path.exists(MEDIA_ROOT):
        os.mkdir(MEDIA_ROOT)


from app.routers import routers

app.include_router(routers, prefix=API_V1_URL)
