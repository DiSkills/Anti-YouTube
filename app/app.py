from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import TESTS, API_V1_URL
from app.db import engine, Base

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[''],
    allow_credentials=True,
    allow_methods=[''],
    allow_headers=['*'],
)


@app.on_event('startup')
async def startup():
    async with engine.begin() as conn:
        if not int(TESTS):
            await conn.run_sync(Base.metadata.create_all)


from app.routers import routers

app.include_router(routers, prefix=API_V1_URL)
