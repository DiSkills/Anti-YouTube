import asyncio
import os

from pydantic import EmailStr, EmailError

from app.auth.crud import user_crud
from app.auth.schemas import RegisterAdmin
from app.auth.security import get_password_hash
from app.db import async_session, engine, Base


async def createsuperuser_docker():
    """ Create superuser (docker) """

    async with async_session() as session:
        async with session.begin():
            if len(await user_crud.all(session)):
                return

            username = os.environ.get('USERNAME_ADMIN')
            email = os.environ.get('EMAIL_ADMIN')
            password = os.environ.get('PASSWORD_ADMIN')

            schema = RegisterAdmin(
                password=password,
                confirm_password=password,
                username=username,
                email=email,
                about='',
                send_message=False,
            )
            del schema.confirm_password

            await user_crud.create(session, schema, password=get_password_hash(schema.password))


async def createsuperuser():
    """ Create superuser online (terminal) """

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        async with session.begin():
            while True:
                username = input('Please input username: ')
                if not await user_crud.exists(session, username=username):
                    break
                print('Username exists')

            while True:
                email = input('Please input email: ')

                try:
                    EmailStr.validate(email)
                    if not await user_crud.exists(session, email=email):
                        break
                except EmailError as error:
                    print('Email not validate')
                    continue

                print('Email exists')

            while True:
                password = input('Please input password: ')
                confirm_password = input('Please input confirm_password: ')
                if len(password) > 8 and confirm_password == password:
                    break
                print('Passwords mismatch or length passwords less 8!')
            schema = RegisterAdmin(
                password=password,
                confirm_password=confirm_password,
                username=username,
                email=email,
                about='',
                send_message=False,
            )
            del schema.confirm_password

            await user_crud.create(session, schema, password=get_password_hash(schema.password))

            print('Superuser has been created')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(createsuperuser())
    finally:
        print("Exit")
