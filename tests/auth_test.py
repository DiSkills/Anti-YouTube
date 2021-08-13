import asyncio
from unittest import TestCase

import jwt
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.app import app
from app.auth.api import (
    register,
    activate,
    login,
    refresh,
    follow,
    unfollow,
    create_reset_password,
    verify_password_reset,
    get_username,
    get_data,
    change_data,
)
from app.auth.crud import user_crud, verification_crud
from app.auth.permission import is_authenticated, is_active, is_superuser
from app.auth.schemas import RegisterUser, VerificationUUID, LoginUser, RefreshToken, Password, ChangeUserDataResponse, \
    ChangeUserData
from app.auth.tokens import ALGORITHM, create_password_reset_token
from app.config import API_V1_URL, SECRET_KEY
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

    def test_reset_password_request(self):
        self.client.post(self.url + '/register', json=self.data)

        # Create reset password

        response = self.client.get(self.url + f'/request-password-reset?email={self.data["email"]}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'msg': 'Email send'})

        response = self.client.get(self.url + f'/request-password-reset?email=test@example.ru')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'User not found'})

        # Verify reset password

        token = create_password_reset_token(self.data['email'])
        response = self.client.post(
            self.url + f'/password-reset?token={token}',
            json={'password': 'test123456', 'confirm_password': 'test123456'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'msg': 'Password has been reset'})

        tokens = self.client.post(
            self.url + '/login', json={'username': 'test', 'password': 'test123456'}
        ).json()

        response = self.client.post(
            self.url + f'/password-reset?token={tokens["access_token"]}',
            json={'password': 'test123456', 'confirm_password': 'test123456'}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Reset token not found'})

        response = self.client.post(
            self.url + f'/password-reset?token={tokens["refresh_token"]}',
            json={'password': 'test123456', 'confirm_password': 'test123456'}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Reset token not found'})

        self.loop(user_crud.remove(self.session, id=1))
        self.loop(self.session.commit())

        response = self.client.post(
            self.url + f'/password-reset?token={token}',
            json={'password': 'test123456', 'confirm_password': 'test123456'}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'User not found'})

    def test_reset_password(self):
        self.client.post(self.url + '/register', json=self.data)

        # Create reset password

        response = self.loop(create_reset_password(self.data["email"]))
        self.assertEqual(response, {'msg': 'Email send'})

        with self.assertRaises(HTTPException) as error:
            self.loop(create_reset_password('test@example.ru'))

        # Verify reset password

        token = create_password_reset_token(self.data['email'])
        response = self.loop(
            verify_password_reset(token, Password(password='test123456', confirm_password='test123456'))
        )
        self.assertEqual(response, {'msg': 'Password has been reset'})

        tokens = self.client.post(
            self.url + '/login', json={'username': 'test', 'password': 'test123456'}
        ).json()

        with self.assertRaises(HTTPException) as error:
            self.loop(
                verify_password_reset(
                    tokens['access_token'], Password(password='test123456', confirm_password='test123456')
                )
            )

        with self.assertRaises(HTTPException) as error:
            self.loop(
                verify_password_reset(
                    tokens['refresh_token'], Password(password='test123456', confirm_password='test123456')
                )
            )

        self.loop(user_crud.remove(self.session, id=1))
        self.loop(self.session.commit())

        with self.assertRaises(HTTPException) as error:
            self.loop(
                verify_password_reset(token, Password(password='test123456', confirm_password='test123456'))
            )

    def test_following_request(self):
        self.client.post(self.url + '/register', json=self.data)
        tokens = self.client.post(self.url + '/login', json={'username': 'test', 'password': 'test1234'})
        verification = self.loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})

        self.client.post(self.url + '/register', json={**self.data, 'username': 'test2', 'email': 'test2@example.com'})

        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

        user_1 = self.loop(user_crud.get(self.session, id=1))
        user_2 = self.loop(user_crud.get(self.session, id=2))
        self.assertEqual(self.loop(user_1.is_following(self.session, user_2)), False)

        # Follow

        response = self.client.post(self.url + '/follow?to_id=2', headers=headers)
        self.assertEqual(response.json(), {'msg': 'You follow to user'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.loop(user_1.is_following(self.session, user_2)), True)

        response = self.client.post(self.url + '/follow?to_id=2', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'You are already followed'})
        self.assertEqual(self.loop(user_1.is_following(self.session, user_2)), True)

        response = self.client.post(self.url + '/follow?to_id=1', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'You not follow to self'})

        response = self.client.post(self.url + '/follow?to_id=4', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Follow to user not found'})

        # Unfollow

        self.assertEqual(self.loop(user_1.is_following(self.session, user_2)), True)
        response = self.client.post(self.url + '/unfollow?to_id=2', headers=headers)
        self.assertEqual(response.json(), {'msg': 'You unfollow to user'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.loop(user_1.is_following(self.session, user_2)), False)

        response = self.client.post(self.url + '/unfollow?to_id=2', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'You are already unfollowed'})
        self.assertEqual(self.loop(user_1.is_following(self.session, user_2)), False)

        response = self.client.post(self.url + '/unfollow?to_id=1', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'You not unfollow to self'})

        response = self.client.post(self.url + '/unfollow?to_id=4', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Unfollow to user not found'})

    def test_following(self):
        self.client.post(self.url + '/register', json=self.data)

        verification = self.loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})

        self.client.post(self.url + '/register', json={**self.data, 'username': 'test2', 'email': 'test2@example.com'})

        user_1 = self.loop(user_crud.get(self.session, id=1))
        user_2 = self.loop(user_crud.get(self.session, id=2))
        self.assertEqual(self.loop(user_1.is_following(self.session, user_2)), False)

        # Follow

        response = self.loop(follow(user_2.id, user_1))
        self.assertEqual(response, {'msg': 'You follow to user'})
        self.assertEqual(self.loop(user_1.is_following(self.session, user_2)), True)

        with self.assertRaises(HTTPException) as error:
            self.loop(follow(user_2.id, user_1))

        with self.assertRaises(HTTPException) as error:
            self.loop(follow(user_1.id, user_1))

        with self.assertRaises(HTTPException) as error:
            self.loop(follow(4, user_1))

        # Unfollow

        self.assertEqual(self.loop(user_1.is_following(self.session, user_2)), True)
        response = self.loop(unfollow(user_2.id, user_1))
        self.assertEqual(response, {'msg': 'You unfollow to user'})
        self.assertEqual(self.loop(user_1.is_following(self.session, user_2)), False)

        with self.assertRaises(HTTPException) as error:
            self.loop(unfollow(user_2.id, user_1))

        with self.assertRaises(HTTPException) as error:
            self.loop(unfollow(user_1.id, user_1))

        with self.assertRaises(HTTPException) as error:
            self.loop(unfollow(4, user_1))

    def test_permission(self):
        with self.assertRaises(HTTPException) as error:
            self.loop(is_authenticated('test'))

        self.client.post(self.url + '/register', json=self.data)
        tokens = self.client.post(self.url + '/login', json={'username': 'test', 'password': 'test1234'})
        response = self.loop(is_authenticated(tokens.json()['access_token']))
        self.assertEqual(response.id, 1)

        with self.assertRaises(HTTPException) as error:
            self.loop(is_authenticated(tokens.json()['refresh_token']))

        with self.assertRaises(HTTPException) as error:
            token = create_password_reset_token(self.data['email'])
            self.loop(is_authenticated(token))

        with self.assertRaises(HTTPException) as error:
            self.loop(is_active(self.loop(is_authenticated(tokens.json()['access_token']))))

        verification = self.loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})

        response = self.loop(is_active(self.loop(is_authenticated(tokens.json()['access_token']))))
        self.assertEqual(response.id, 1)

        with self.assertRaises(HTTPException) as error:
            self.loop(is_superuser(self.loop(is_active(self.loop(is_authenticated(tokens.json()['access_token']))))))

        self.loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        self.loop(self.session.commit())
        response = self.loop(
            is_superuser(self.loop(is_active(self.loop(is_authenticated(tokens.json()['access_token'])))))
        )
        self.assertEqual(response.id, 1)

        with self.assertRaises(HTTPException) as error:
            self.loop(user_crud.remove(self.session, id=1))
            self.loop(self.session.commit())
            self.loop(is_authenticated(tokens.json()['access_token']))

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

    def test_login_request(self):
        self.client.post(self.url + '/register', json=self.data)

        response = self.client.post(self.url + '/login', json={'username': 'test', 'password': 'test1234'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['token_type'], 'bearer')
        self.assertEqual('access_token' and 'refresh_token' in response.json(), True)
        self.assertEqual(
            jwt.decode(response.json()['access_token'], SECRET_KEY, algorithms=[ALGORITHM])['user_id'], 1
        )
        self.assertEqual(
            jwt.decode(response.json()['refresh_token'], SECRET_KEY, algorithms=[ALGORITHM])['username'], 'test'
        )

        response = self.client.post(self.url + '/login', json={'username': 'admin', 'password': 'test1234'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'User not found'})

        response = self.client.post(self.url + '/login', json={'username': 'test', 'password': 'test'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Password mismatch'})

    def test_login(self):
        self.client.post(self.url + '/register', json=self.data)

        response = self.loop(login(LoginUser(username='test', password='test1234')))
        self.assertEqual(response['token_type'], 'bearer')
        self.assertEqual('access_token' and 'refresh_token' in response, True)
        self.assertEqual(
            jwt.decode(response['access_token'], SECRET_KEY, algorithms=[ALGORITHM])['user_id'], 1
        )
        self.assertEqual(
            jwt.decode(response['refresh_token'], SECRET_KEY, algorithms=[ALGORITHM])['username'], 'test'
        )

        with self.assertRaises(HTTPException) as error:
            self.loop(login(LoginUser(username='admin', password='test1234')))

        with self.assertRaises(HTTPException) as error:
            self.loop(login(LoginUser(username='test', password='test')))

    def test_refresh_token_request(self):
        self.client.post(self.url + '/register', json=self.data)

        tokens = self.client.post(self.url + '/login', json={'username': 'test', 'password': 'test1234'})

        response = self.client.post(self.url + '/refresh', json={'refresh_token': tokens.json()['refresh_token']})
        self.assertEqual('access_token' in response.json(), True)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            jwt.decode(response.json()['access_token'], SECRET_KEY, algorithms=[ALGORITHM])['user_id'], 1
        )

        response = self.client.post(self.url + '/refresh', json={'refresh_token': 'token'})
        self.assertEqual(response.json(), {'detail': 'Token lifetime ended'})
        self.assertEqual(response.status_code, 401)

        response = self.client.post(self.url + '/refresh', json={'refresh_token': tokens.json()['access_token']})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Refresh token not found'})

        verification = self.loop(verification_crud.get(self.session, user_id=1))

        self.client.post(self.url + '/activate', json={'uuid': verification.uuid})

        self.loop(user_crud.remove(self.session, id=1))
        self.loop(self.session.commit())

        response = self.client.post(self.url + '/refresh', json={'refresh_token': tokens.json()['refresh_token']})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'User not found'})

    def test_refresh_token(self):
        self.client.post(self.url + '/register', json=self.data)

        tokens = self.client.post(self.url + '/login', json={'username': 'test', 'password': 'test1234'})

        response = self.loop(refresh(RefreshToken(refresh_token=tokens.json()['refresh_token'])))
        self.assertEqual('access_token' in response, True)

        self.assertEqual(
            jwt.decode(response['access_token'], SECRET_KEY, algorithms=[ALGORITHM])['user_id'], 1
        )

        with self.assertRaises(HTTPException) as error:
            self.loop(refresh(RefreshToken(refresh_token='token')))

        with self.assertRaises(HTTPException) as error:
            self.loop(refresh(RefreshToken(refresh_token=tokens.json()['access_token'])))

        verification = self.loop(verification_crud.get(self.session, user_id=1))

        self.client.post(self.url + '/activate', json={'uuid': verification.uuid})

        self.loop(user_crud.remove(self.session, id=1))
        self.loop(self.session.commit())

        with self.assertRaises(HTTPException) as error:
            self.loop(refresh(RefreshToken(refresh_token=tokens.json()['refresh_token'])))

    def test_get_username_request(self):
        self.client.post(self.url + '/register', json=self.data)

        response = self.client.post(self.url + f'/username?email={self.data["email"]}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'msg': 'Email send'})

        response = self.client.post(self.url + f'/username?email=test2@example.com')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'User not found'})

    def test_get_username(self):
        self.client.post(self.url + '/register', json=self.data)

        response = self.loop(get_username(self.data['email']))
        self.assertEqual(response, {'msg': 'Email send'})

        with self.assertRaises(HTTPException) as error:
            self.loop(get_username('test2@example.com'))

    def test_change_data_request(self):
        self.client.post(self.url + '/register', json=self.data)

        verification = self.loop(verification_crud.get(self.session, user_id=1))
        self.client.post(self.url + '/activate', json={'uuid': verification.uuid})

        tokens = self.client.post(self.url + '/login', json={'username': 'test', 'password': 'test1234'})

        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

        # Get data
        response = self.client.get(self.url + '/change-data', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ChangeUserDataResponse(**self.data, avatar=''))

        # Put data
        response = self.client.put(self.url + '/change-data', headers=headers, json={
            'send_message': False, 'about': 'test',
        })
        self.assertFalse(response.json()['send_message'])
        self.assertEqual(response.json()['about'], 'test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), ChangeUserDataResponse(**{**self.data, 'send_message': False, 'about': 'test'}, avatar='')
        )

    def test_change_data(self):
        self.client.post(self.url + '/register', json=self.data)

        verification = self.loop(verification_crud.get(self.session, user_id=1))
        self.client.post(self.url + '/activate', json={'uuid': verification.uuid})

        user = self.loop(user_crud.get(self.session, id=1))

        # Get data
        response = self.loop(get_data(user))
        self.assertEqual(response, user.__dict__)

        # Put data
        response = self.loop(change_data(ChangeUserData(send_message=False, about='test'), user))
        self.loop(self.session.commit())
        self.assertFalse(response['send_message'])
        self.assertEqual(response['about'], 'test')

        user = self.loop(user_crud.get(self.session, id=1))

        self.assertEqual(response['send_message'], user.send_message)
        self.assertEqual(response['about'], user.about)
