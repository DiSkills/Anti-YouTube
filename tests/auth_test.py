import os
import shutil
from unittest import TestCase

import jwt
from fastapi import HTTPException, UploadFile
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
    upload_avatar,
    subscriptions,
)
from app.auth.crud import user_crud, verification_crud
from app.auth.permission import is_authenticated, is_active, is_superuser
from app.auth.schemas import (
    RegisterUser,
    VerificationUUID,
    RefreshToken,
    Password,
    ChangeUserDataResponse,
    ChangeUserData,
)
from app.auth.tokens import ALGORITHM, create_password_reset_token
from app.config import API_V1_URL, SECRET_KEY, MEDIA_ROOT
from app.db import engine, AsyncSession
from tests import create_all, drop_all, async_loop


class AuthTestCase(TestCase):

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
        self.video_data = {
            'title': 'Anti-YouTube',
            'description': 'Hello world!',
            'category_id': 1,
        }
        self.url = API_V1_URL + '/auth'
        async_loop(create_all())
        os.mkdir(MEDIA_ROOT)

    def tearDown(self) -> None:
        async_loop(self.session.close())
        async_loop(drop_all())
        shutil.rmtree(MEDIA_ROOT)

    def test_subscriptions(self):
        self.client.post(self.url + '/register', json=self.data)
        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

        self.client.post(self.url + '/register', json={**self.data, 'username': 'test2', 'email': 'test2@example.com'})
        self.client.post(self.url + '/register', json={**self.data, 'username': 'test3', 'email': 'test3@example.com'})
        verification = async_loop(verification_crud.get(self.session, user_id=2)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})

        user_1 = async_loop(user_crud.get(self.session, id=1))

        response = async_loop(subscriptions(user_1))
        self.assertEqual(response, [])

        async_loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        async_loop(self.session.commit())
        self.client.post(API_V1_URL + '/categories/', json={'name': 'FastAPI'}, headers=headers)

        tokens = self.client.post(self.url + '/login', data={'username': 'test2', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                self.client.post(
                    API_V1_URL + '/videos/',
                    headers=headers,
                    data=self.video_data,
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )
        self.client.post(self.url + '/follow?to_id=3', headers=headers)

        tokens = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        self.client.post(self.url + '/follow?to_id=2', headers=headers)
        self.client.post(self.url + '/follow?to_id=3', headers=headers)

        response = async_loop(subscriptions(async_loop(user_crud.get(self.session, id=1))))
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0]['user']['id'], 3)
        self.assertEqual(len(response[0]['videos']), 0)
        self.assertEqual(response[1]['user']['id'], 2)
        self.assertEqual(len(response[1]['videos']), 1)

        user_2 = async_loop(user_crud.get(self.session, id=2))
        response = async_loop(subscriptions(user_2))
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['user']['id'], 3)
        self.assertEqual(len(response[0]['videos']), 0)

    def test_subscriptions_request(self):
        self.client.post(self.url + '/register', json=self.data)
        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

        self.client.post(self.url + '/register', json={**self.data, 'username': 'test2', 'email': 'test2@example.com'})
        self.client.post(self.url + '/register', json={**self.data, 'username': 'test3', 'email': 'test3@example.com'})
        verification = async_loop(verification_crud.get(self.session, user_id=2)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})

        response = self.client.get(self.url + '/followed', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        async_loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        async_loop(self.session.commit())
        self.client.post(API_V1_URL + '/categories/', json={'name': 'FastAPI'}, headers=headers)

        tokens = self.client.post(self.url + '/login', data={'username': 'test2', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                self.client.post(
                    API_V1_URL + '/videos/',
                    headers=headers,
                    data=self.video_data,
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )
        self.client.post(self.url + '/follow?to_id=3', headers=headers)

        tokens = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        self.client.post(self.url + '/follow?to_id=2', headers=headers)
        self.client.post(self.url + '/follow?to_id=3', headers=headers)

        response = self.client.get(self.url + '/followed', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]['user']['id'], 3)
        self.assertEqual(len(response.json()[0]['videos']), 0)
        self.assertEqual(response.json()[1]['user']['id'], 2)
        self.assertEqual(len(response.json()[1]['videos']), 1)

        tokens = self.client.post(self.url + '/login', data={'username': 'test2', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        response = self.client.get(self.url + '/followed', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['user']['id'], 3)
        self.assertEqual(len(response.json()[0]['videos']), 0)

    def test_channel(self):
        # Get channel
        self.client.post(self.url + '/register', json=self.data)
        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test1234'})

        async_loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        async_loop(self.session.commit())

        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        self.client.post(API_V1_URL + '/categories/', json={'name': 'FastAPI'}, headers=headers)

        self.client.post(self.url + '/register', json={**self.data, 'username': 'test2', 'email': 'test2@example.com'})
        verification = async_loop(verification_crud.get(self.session, user_id=2)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(self.url + '/login', data={'username': 'test2', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

        response = self.client.get(self.url + '/channel?pk=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], 2)
        self.assertEqual(response.json()['count_videos'], 0)
        self.assertEqual(response.json()['views'], 0)

        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                self.client.post(
                    API_V1_URL + '/videos/',
                    headers=headers,
                    data=self.video_data,
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )
        response = self.client.get(self.url + '/channel?pk=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], 2)
        self.assertEqual(response.json()['count_videos'], 1)
        self.assertEqual(response.json()['views'], 0)
        self.assertEqual(response.json()['is_following'], None)

        self.client.post(API_V1_URL + '/videos/add-to-history?pk=1', headers=headers)
        response = self.client.get(self.url + '/channel?pk=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], 2)
        self.assertEqual(response.json()['count_videos'], 1)
        self.assertEqual(response.json()['views'], 1)
        self.assertEqual(response.json()['is_following'], None)

        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                self.client.post(
                    API_V1_URL + '/videos/',
                    headers=headers,
                    data=self.video_data,
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )
        response = self.client.get(self.url + '/channel?pk=2')
        self.assertEqual(response.json()['count_videos'], 2)

        # Self
        response = self.client.get(self.url + '/channel?pk=2', headers=headers)
        self.assertEqual(response.json()['is_following'], 3)

        # Unfollow
        tokens = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        response = self.client.get(self.url + '/channel?pk=2', headers=headers)
        self.assertEqual(response.json()['is_following'], 0)

        # Follow
        self.client.post(self.url + '/follow?to_id=2', headers=headers)
        response = self.client.get(self.url + '/channel?pk=2', headers=headers)
        self.assertEqual(response.json()['is_following'], 1)

        self.client.post(API_V1_URL + '/videos/add-to-history?pk=1', headers=headers)
        self.client.post(API_V1_URL + '/videos/add-to-history?pk=1', headers=headers)
        response = self.client.get(self.url + '/channel?pk=2')
        self.assertEqual(response.json()['views'], 3)

        response = self.client.get(self.url + '/channel?pk=143')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'User not found'})

        self.client.post(self.url + '/register', json={**self.data, 'username': 'test3', 'email': 'test3@example.com'})
        response = self.client.get(self.url + '/channel?pk=3')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['views'], 0)
        self.assertEqual(response.json()['count_videos'], 0)

        # Get videos
        response = self.client.get(self.url + '/channel/videos/3')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        response = self.client.get(self.url + '/channel/videos/2')
        self.assertEqual(response.json()[0]['id'], 2)
        self.assertEqual(response.json()[1]['id'], 1)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]['user']['username'], 'test2')
        self.assertEqual(response.json()[1]['user']['username'], 'test2')

        response = self.client.get(self.url + '/channel/videos/143')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'User not found'})

    def test_upload_avatar_requests(self):
        self.client.post(self.url + '/register', json=self.data)
        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test1234'})

        user = async_loop(user_crud.get(self.session, id=1))

        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

        self.assertEqual(os.path.exists(user.avatar), False)

        with open('tests/image.png', 'rb') as f:
            response = self.client.post(
                self.url + '/avatar', headers=headers, files={'avatar': ('image.png', f, 'image/png')}
            )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()['avatar'], user.avatar)

        self.assertEqual(os.path.exists(response.json()['avatar']), True)

        with open('tests/image.png', 'rb') as f:
            response_2 = self.client.post(
                self.url + '/avatar', headers=headers, files={'avatar': ('image.png', f, 'image/png')}
            )
        self.assertEqual(response_2.status_code, 200)

        self.assertEqual(os.path.exists(response.json()['avatar']), False)
        self.assertEqual(os.path.exists(response_2.json()['avatar']), True)

        with open('tests/image.gif', 'rb') as f:
            response = self.client.post(
                self.url + '/avatar', headers=headers, files={'avatar': ('image.gif', f, 'image/gif')}
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Avatar only format in jpeg or png'})

        self.assertEqual(os.path.exists(response_2.json()['avatar']), True)

    def test_upload_image(self):
        self.client.post(self.url + '/register', json=self.data)
        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})
        user = async_loop(user_crud.get(self.session, id=1))

        self.assertEqual(os.path.exists(user.avatar), False)

        with open('tests/image.png', 'rb') as f:
            response = async_loop(upload_avatar(UploadFile(f.name, f, content_type='image/png'), user))
        self.assertNotEqual(response['avatar'], user.avatar)

        self.assertEqual(os.path.exists(response['avatar']), True)
        async_loop(self.session.commit())

        with open('tests/image.png', 'rb') as f:
            user = async_loop(user_crud.get(self.session, id=1))
            response_2 = async_loop(upload_avatar(UploadFile(f.name, f, content_type='image/png'), user))
        self.assertNotEqual(response_2['avatar'], user.avatar)
        self.assertNotEqual(response_2['avatar'], response['avatar'])

        self.assertEqual(os.path.exists(response_2['avatar']), True)
        self.assertEqual(os.path.exists(response['avatar']), False)

        with self.assertRaises(HTTPException) as error:
            with open('tests/image.gif', 'rb') as f:
                async_loop(upload_avatar(UploadFile(f.name, f, content_type='image/gif'), user))

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
            self.url + '/login', data={'username': 'test', 'password': 'test123456'}
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

        async_loop(user_crud.remove(self.session, id=1))
        async_loop(self.session.commit())

        response = self.client.post(
            self.url + f'/password-reset?token={token}',
            json={'password': 'test123456', 'confirm_password': 'test123456'}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'User not found'})

    def test_reset_password(self):
        self.client.post(self.url + '/register', json=self.data)

        # Create reset password

        response = async_loop(create_reset_password(self.data["email"]))
        self.assertEqual(response, {'msg': 'Email send'})

        with self.assertRaises(HTTPException) as error:
            async_loop(create_reset_password('test@example.ru'))

        # Verify reset password

        token = create_password_reset_token(self.data['email'])
        response = async_loop(
            verify_password_reset(token, Password(password='test123456', confirm_password='test123456'))
        )
        self.assertEqual(response, {'msg': 'Password has been reset'})

        tokens = self.client.post(
            self.url + '/login', data={'username': 'test', 'password': 'test123456'}
        ).json()

        with self.assertRaises(HTTPException) as error:
            async_loop(
                verify_password_reset(
                    tokens['access_token'], Password(password='test123456', confirm_password='test123456')
                )
            )

        with self.assertRaises(HTTPException) as error:
            async_loop(
                verify_password_reset(
                    tokens['refresh_token'], Password(password='test123456', confirm_password='test123456')
                )
            )

        async_loop(user_crud.remove(self.session, id=1))
        async_loop(self.session.commit())

        with self.assertRaises(HTTPException) as error:
            async_loop(
                verify_password_reset(token, Password(password='test123456', confirm_password='test123456'))
            )

    def test_following_request(self):
        self.client.post(self.url + '/register', json=self.data)
        tokens = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test1234'})
        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})

        self.client.post(self.url + '/register', json={**self.data, 'username': 'test2', 'email': 'test2@example.com'})

        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

        user_1 = async_loop(user_crud.get(self.session, id=1))
        user_2 = async_loop(user_crud.get(self.session, id=2))
        self.assertEqual(async_loop(user_1.is_following(self.session, user_2)), False)

        # Follow

        response = self.client.post(self.url + '/follow?to_id=2', headers=headers)
        self.assertEqual(response.json(), {'msg': 'You follow to user'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(async_loop(user_1.is_following(self.session, user_2)), True)

        response = self.client.post(self.url + '/follow?to_id=2', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'You are already followed'})
        self.assertEqual(async_loop(user_1.is_following(self.session, user_2)), True)

        response = self.client.post(self.url + '/follow?to_id=1', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'You not follow to self'})

        response = self.client.post(self.url + '/follow?to_id=4', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Follow to user not found'})

        # Unfollow

        self.assertEqual(async_loop(user_1.is_following(self.session, user_2)), True)
        response = self.client.post(self.url + '/unfollow?to_id=2', headers=headers)
        self.assertEqual(response.json(), {'msg': 'You unfollow to user'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(async_loop(user_1.is_following(self.session, user_2)), False)

        response = self.client.post(self.url + '/unfollow?to_id=2', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'You are already unfollowed'})
        self.assertEqual(async_loop(user_1.is_following(self.session, user_2)), False)

        response = self.client.post(self.url + '/unfollow?to_id=1', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'You not unfollow to self'})

        response = self.client.post(self.url + '/unfollow?to_id=4', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Unfollow to user not found'})

    def test_following(self):
        self.client.post(self.url + '/register', json=self.data)

        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})

        self.client.post(self.url + '/register', json={**self.data, 'username': 'test2', 'email': 'test2@example.com'})

        user_1 = async_loop(user_crud.get(self.session, id=1))
        user_2 = async_loop(user_crud.get(self.session, id=2))
        self.assertEqual(async_loop(user_1.is_following(self.session, user_2)), False)

        # Follow

        response = async_loop(follow(user_2.id, user_1))
        self.assertEqual(response, {'msg': 'You follow to user'})
        self.assertEqual(async_loop(user_1.is_following(self.session, user_2)), True)

        with self.assertRaises(HTTPException) as error:
            async_loop(follow(user_2.id, user_1))

        with self.assertRaises(HTTPException) as error:
            async_loop(follow(user_1.id, user_1))

        with self.assertRaises(HTTPException) as error:
            async_loop(follow(4, user_1))

        # Unfollow

        self.assertEqual(async_loop(user_1.is_following(self.session, user_2)), True)
        response = async_loop(unfollow(user_2.id, user_1))
        self.assertEqual(response, {'msg': 'You unfollow to user'})
        self.assertEqual(async_loop(user_1.is_following(self.session, user_2)), False)

        with self.assertRaises(HTTPException) as error:
            async_loop(unfollow(user_2.id, user_1))

        with self.assertRaises(HTTPException) as error:
            async_loop(unfollow(user_1.id, user_1))

        with self.assertRaises(HTTPException) as error:
            async_loop(unfollow(4, user_1))

    def test_permission(self):
        with self.assertRaises(HTTPException) as error:
            async_loop(is_authenticated('test'))

        self.client.post(self.url + '/register', json=self.data)
        tokens = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test1234'})
        response = async_loop(is_authenticated(tokens.json()['access_token']))
        self.assertEqual(response.id, 1)

        with self.assertRaises(HTTPException) as error:
            async_loop(is_authenticated(tokens.json()['refresh_token']))

        with self.assertRaises(HTTPException) as error:
            token = create_password_reset_token(self.data['email'])
            async_loop(is_authenticated(token))

        with self.assertRaises(HTTPException) as error:
            async_loop(is_active(async_loop(is_authenticated(tokens.json()['access_token']))))

        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})

        response = async_loop(is_active(async_loop(is_authenticated(tokens.json()['access_token']))))
        self.assertEqual(response.id, 1)

        with self.assertRaises(HTTPException) as error:
            async_loop(is_superuser(async_loop(is_active(async_loop(is_authenticated(tokens.json()['access_token']))))))

        async_loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        async_loop(self.session.commit())
        response = async_loop(
            is_superuser(async_loop(is_active(async_loop(is_authenticated(tokens.json()['access_token'])))))
        )
        self.assertEqual(response.id, 1)

        with self.assertRaises(HTTPException) as error:
            async_loop(user_crud.remove(self.session, id=1))
            async_loop(self.session.commit())
            async_loop(is_authenticated(tokens.json()['access_token']))

    def test_register_request(self):

        self.assertEqual(async_loop(user_crud.exists(self.session, id=1)), False)
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 0)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 0)
        self.assertEqual(async_loop(verification_crud.exists(self.session, id=1)), False)

        response = self.client.post(self.url + '/register', json=self.data)

        self.assertEqual(async_loop(user_crud.exists(self.session, id=1)), True)
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 1)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 1)
        self.assertEqual(async_loop(verification_crud.exists(self.session, id=1)), True)
        self.assertEqual(response.json(), {'msg': 'Send email for activate account'})
        self.assertEqual(response.status_code, 201)

        response = self.client.post(self.url + '/register', json=self.data)
        self.assertEqual(response.json(), {'detail': 'Username exist'})
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 1)
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.url + '/register', json={**self.data, 'username': 'test2'})
        self.assertEqual(response.json(), {'detail': 'Email exist'})
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 1)
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.url + '/register', json={**self.data, 'username': 'test2', 'email': 'test'})
        self.assertEqual(response.json()['detail'][0]['msg'], 'value is not a valid email address')
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 1)
        self.assertEqual(response.status_code, 422)

        response = self.client.post(
            self.url + '/register', json={
                **self.data, 'username': 'test2', 'email': 'test@test.com', 'password': 'test'
            }
        )
        self.assertEqual(response.json()['detail'][0]['msg'], 'Min length password is 8 chars')
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 1)
        self.assertEqual(response.status_code, 422)

        response = self.client.post(
            self.url + '/register', json={
                **self.data, 'username': 'test2', 'email': 'test@test.com', 'confirm_password': 'test'
            }
        )
        self.assertEqual(response.json()['detail'][0]['msg'], 'Passwords do not match')
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 1)
        self.assertEqual(response.status_code, 422)
        
    def test_register(self):

        self.assertEqual(async_loop(user_crud.exists(self.session, id=1)), False)
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 0)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 0)
        self.assertEqual(async_loop(verification_crud.exists(self.session, id=1)), False)

        response = async_loop(register(RegisterUser(**self.data)))

        self.assertEqual(async_loop(user_crud.exists(self.session, id=1)), True)
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 1)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 1)
        self.assertEqual(async_loop(verification_crud.exists(self.session, id=1)), True)
        self.assertEqual(response, {'msg': 'Send email for activate account'})

        with self.assertRaises(HTTPException) as error:
            async_loop(register(RegisterUser(**self.data)))

        with self.assertRaises(HTTPException) as error:
            async_loop(register(RegisterUser(**{**self.data, 'username': 'test2'})))

        with self.assertRaises(ValueError) as error:
            async_loop(register(RegisterUser(**{**self.data, 'username': 'test2', 'email': 'test'})))

        with self.assertRaises(ValueError) as error:
            async_loop(
                register(
                    RegisterUser(**{**self.data, 'username': 'test2', 'email': 'test@test.com', 'password': 'test'})
                )
            )

        with self.assertRaises(ValueError) as error:
            async_loop(
                register(
                    RegisterUser(
                        **{**self.data, 'username': 'test2', 'email': 'test@test.com', 'confirm_password': 'test'}
                    )
                )
            )

    def test_activate_request(self):
        self.client.post(self.url + '/register', json=self.data)

        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__

        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 1)

        self.assertEqual(async_loop(user_crud.get(self.session, id=1)).__dict__['is_active'], False)

        response = self.client.post(self.url + '/activate', json={'uuid': 'uuid'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Verification not found'})
        self.assertEqual(async_loop(user_crud.get(self.session, id=1)).__dict__['is_active'], False)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 1)

        response = self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'msg': 'Account has been is activated'})
        self.assertEqual(async_loop(user_crud.get(self.session, id=1)).__dict__['is_active'], True)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 0)

        response = self.client.post(self.url + '/activate', json={'uuid': verification['uuid']})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Verification not found'})

    def test_activate(self):
        self.client.post(self.url + '/register', json=self.data)

        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__

        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 1)

        self.assertEqual(async_loop(user_crud.get(self.session, id=1)).__dict__['is_active'], False)

        with self.assertRaises(HTTPException) as error:
            async_loop(activate(VerificationUUID(uuid='uuid')))
        self.assertEqual(async_loop(user_crud.get(self.session, id=1)).__dict__['is_active'], False)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 1)

        response = async_loop(activate(VerificationUUID(uuid=verification['uuid'])))
        self.assertEqual(response, {'msg': 'Account has been is activated'})
        self.assertEqual(async_loop(user_crud.get(self.session, id=1)).__dict__['is_active'], True)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 0)

    def test_login_request(self):
        self.client.post(self.url + '/register', json=self.data)

        response = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test1234'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['token_type'], 'bearer')
        self.assertEqual('access_token' and 'refresh_token' in response.json(), True)
        self.assertEqual(
            jwt.decode(response.json()['access_token'], SECRET_KEY, algorithms=[ALGORITHM])['user_id'], 1
        )
        self.assertEqual(
            jwt.decode(response.json()['refresh_token'], SECRET_KEY, algorithms=[ALGORITHM])['username'], 'test'
        )

        response = self.client.post(self.url + '/login', data={'username': 'admin', 'password': 'test1234'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'User not found'})

        response = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Password mismatch'})

    def test_login(self):
        self.client.post(self.url + '/register', json=self.data)

        response = async_loop(login(username='test', password='test1234'))
        self.assertEqual(response['token_type'], 'bearer')
        self.assertEqual('access_token' and 'refresh_token' in response, True)
        self.assertEqual(
            jwt.decode(response['access_token'], SECRET_KEY, algorithms=[ALGORITHM])['user_id'], 1
        )
        self.assertEqual(
            jwt.decode(response['refresh_token'], SECRET_KEY, algorithms=[ALGORITHM])['username'], 'test'
        )

        with self.assertRaises(HTTPException) as error:
            async_loop(login(username='admin', password='test1234'))

        with self.assertRaises(HTTPException) as error:
            async_loop(login(username='test', password='test'))

    def test_refresh_token_request(self):
        self.client.post(self.url + '/register', json=self.data)

        tokens = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test1234'})

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

        verification = async_loop(verification_crud.get(self.session, user_id=1))

        self.client.post(self.url + '/activate', json={'uuid': verification.uuid})

        async_loop(user_crud.remove(self.session, id=1))
        async_loop(self.session.commit())

        response = self.client.post(self.url + '/refresh', json={'refresh_token': tokens.json()['refresh_token']})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'User not found'})

    def test_refresh_token(self):
        self.client.post(self.url + '/register', json=self.data)

        tokens = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test1234'})

        response = async_loop(refresh(RefreshToken(refresh_token=tokens.json()['refresh_token'])))
        self.assertEqual('access_token' in response, True)

        self.assertEqual(
            jwt.decode(response['access_token'], SECRET_KEY, algorithms=[ALGORITHM])['user_id'], 1
        )

        with self.assertRaises(HTTPException) as error:
            async_loop(refresh(RefreshToken(refresh_token='token')))

        with self.assertRaises(HTTPException) as error:
            async_loop(refresh(RefreshToken(refresh_token=tokens.json()['access_token'])))

        verification = async_loop(verification_crud.get(self.session, user_id=1))

        self.client.post(self.url + '/activate', json={'uuid': verification.uuid})

        async_loop(user_crud.remove(self.session, id=1))
        async_loop(self.session.commit())

        with self.assertRaises(HTTPException) as error:
            async_loop(refresh(RefreshToken(refresh_token=tokens.json()['refresh_token'])))

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

        response = async_loop(get_username(self.data['email']))
        self.assertEqual(response, {'msg': 'Email send'})

        with self.assertRaises(HTTPException) as error:
            async_loop(get_username('test2@example.com'))

    def test_change_data_request(self):
        self.client.post(self.url + '/register', json=self.data)

        verification = async_loop(verification_crud.get(self.session, user_id=1))
        self.client.post(self.url + '/activate', json={'uuid': verification.uuid})

        tokens = self.client.post(self.url + '/login', data={'username': 'test', 'password': 'test1234'})

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

        verification = async_loop(verification_crud.get(self.session, user_id=1))
        self.client.post(self.url + '/activate', json={'uuid': verification.uuid})

        user = async_loop(user_crud.get(self.session, id=1))

        # Get data
        response = async_loop(get_data(user))
        self.assertEqual(response, user.__dict__)

        # Put data
        response = async_loop(change_data(ChangeUserData(send_message=False, about='test'), user))
        async_loop(self.session.commit())
        self.assertFalse(response['send_message'])
        self.assertEqual(response['about'], 'test')

        user = async_loop(user_crud.get(self.session, id=1))

        self.assertEqual(response['send_message'], user.send_message)
        self.assertEqual(response['about'], user.about)
