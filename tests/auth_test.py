import asyncio
from unittest import TestCase

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.app import app
from app.auth.api import register, activate
from app.auth.crud import user_crud, verification_crud
from app.auth.schemas import RegisterUser, VerificationUUID
from app.config import API_V1_URL
from app.db import Base, engine, AsyncSession


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class AuthTestCase(TestCase):

    def loop(self, function):
        loop = asyncio.get_event_loop()
        try:
            return loop.run_until_complete(function)
        finally:
            pass

    def setUp(self) -> None:
        self.session = AsyncSession(engine)
        self.client = TestClient(app)
        self.data = {
            'password': 'test1234',
            'confirm_password': 'test1234',
            'username': 'test',
            'email': 'test@example.com',
            'about': 'string',
            'send_message': True
        }
        self.url = API_V1_URL + '/auth'
        self.loop(create_all())

    def tearDown(self) -> None:
        self.loop(self.session.close())
        self.loop(drop_all())

    def test_register_request(self):

        self.assertEqual(self.loop(user_crud.exists(self.session, id=1)), False)
        self.assertEqual(len(self.loop(user_crud.all(self.session))), 0)
        self.assertEqual(len(self.loop(verification_crud.all(self.session))), 0)
        self.assertEqual(self.loop(verification_crud.exists(self.session, id=1)), False)

        response = self.client.post(self.url + '/register', json=self.data)

        self.assertEqual(self.loop(user_crud.exists(self.session, id=1)), True)
        self.assertEqual(len(self.loop(user_crud.all(self.session))), 1)
        self.assertEqual(len(self.loop(verification_crud.all(self.session))), 1)
        self.assertEqual(self.loop(verification_crud.exists(self.session, id=1)), True)
        self.assertEqual(response.json(), {'msg': 'Send email for activate account'})
        self.assertEqual(response.status_code, 201)

        response = self.client.post(self.url + '/register', json=self.data)
        self.assertEqual(response.json(), {'detail': 'Username exist'})
        self.assertEqual(len(self.loop(user_crud.all(self.session))), 1)
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.url + '/register', json={**self.data, 'username': 'test2'})
        self.assertEqual(response.json(), {'detail': 'Email exist'})
        self.assertEqual(len(self.loop(user_crud.all(self.session))), 1)
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.url + '/register', json={**self.data, 'username': 'test2', 'email': 'test'})
        self.assertEqual(response.json()['detail'][0]['msg'], 'value is not a valid email address')
        self.assertEqual(len(self.loop(user_crud.all(self.session))), 1)
        self.assertEqual(response.status_code, 422)

        response = self.client.post(
            self.url + '/register', json={
                **self.data, 'username': 'test2', 'email': 'test@test.com', 'password': 'test'
            }
        )
        self.assertEqual(response.json()['detail'][0]['msg'], 'Min length password is 8 chars')
        self.assertEqual(len(self.loop(user_crud.all(self.session))), 1)
        self.assertEqual(response.status_code, 422)

        response = self.client.post(
            self.url + '/register', json={
                **self.data, 'username': 'test2', 'email': 'test@test.com', 'confirm_password': 'test'
            }
        )
        self.assertEqual(response.json()['detail'][0]['msg'], 'Passwords do not match')
        self.assertEqual(len(self.loop(user_crud.all(self.session))), 1)
        self.assertEqual(response.status_code, 422)
        
    def test_register(self):

        self.assertEqual(self.loop(user_crud.exists(self.session, id=1)), False)
        self.assertEqual(len(self.loop(user_crud.all(self.session))), 0)
        self.assertEqual(len(self.loop(verification_crud.all(self.session))), 0)
        self.assertEqual(self.loop(verification_crud.exists(self.session, id=1)), False)

        response = self.loop(register(RegisterUser(**self.data)))

        self.assertEqual(self.loop(user_crud.exists(self.session, id=1)), True)
        self.assertEqual(len(self.loop(user_crud.all(self.session))), 1)
        self.assertEqual(len(self.loop(verification_crud.all(self.session))), 1)
        self.assertEqual(self.loop(verification_crud.exists(self.session, id=1)), True)
        self.assertEqual(response, {'msg': 'Send email for activate account'})

        with self.assertRaises(HTTPException) as error:
            self.loop(register(RegisterUser(**self.data)))

        with self.assertRaises(HTTPException) as error:
            self.loop(register(RegisterUser(**{**self.data, 'username': 'test2'})))

        with self.assertRaises(ValueError) as error:
            self.loop(register(RegisterUser(**{**self.data, 'username': 'test2', 'email': 'test'})))

        with self.assertRaises(ValueError) as error:
            self.loop(
                register(
                    RegisterUser(**{**self.data, 'username': 'test2', 'email': 'test@test.com', 'password': 'test'})
                )
            )

        with self.assertRaises(ValueError) as error:
            self.loop(
                register(
                    RegisterUser(
                        **{**self.data, 'username': 'test2', 'email': 'test@test.com', 'confirm_password': 'test'}
                    )
                )
            )

    def test_activate_request(self):
        self.client.post(self.url + '/register', json=self.data)

        verification = self.loop(verification_crud.get(self.session, user_id=1)).__dict__

        self.assertEqual(len(self.loop(verification_crud.all(self.session))), 1)

        self.assertEqual(self.loop(user_crud.get(self.session, id=1)).__dict__['is_active'], False)

        response = self.client.post(self.url + '/activate', json={'uuid': 'uuid'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Verification not found'})
        self.assertEqual(self.loop(user_crud.get(self.session, id=1)).__dict__['is_active'], False)
        self.assertEqual(len(self.loop(verification_crud.all(self.session))), 1)

        response = self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'msg': 'Account has been is activated'})
        self.assertEqual(self.loop(user_crud.get(self.session, id=1)).__dict__['is_active'], True)
        self.assertEqual(len(self.loop(verification_crud.all(self.session))), 0)

        response = self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Verification not found'})

    def test_activate(self):
        self.client.post(self.url + '/register', json=self.data)

        verification = self.loop(verification_crud.get(self.session, user_id=1)).__dict__

        self.assertEqual(len(self.loop(verification_crud.all(self.session))), 1)

        self.assertEqual(self.loop(user_crud.get(self.session, id=1)).__dict__['is_active'], False)

        with self.assertRaises(HTTPException) as error:
            self.loop(activate(VerificationUUID(uuid='uuid')))
        self.assertEqual(self.loop(user_crud.get(self.session, id=1)).__dict__['is_active'], False)
        self.assertEqual(len(self.loop(verification_crud.all(self.session))), 1)

        response = self.loop(activate(VerificationUUID(uuid=verification['uuid'])))
        self.assertEqual(response, {'msg': 'Account has been is activated'})
        self.assertEqual(self.loop(user_crud.get(self.session, id=1)).__dict__['is_active'], True)
        self.assertEqual(len(self.loop(verification_crud.all(self.session))), 0)
