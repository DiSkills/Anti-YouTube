import asyncio
import os
import shutil
from unittest import TestCase

from fastapi import UploadFile, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.app import app
from app.auth.crud import verification_crud, user_crud
from app.config import MEDIA_ROOT, API_V1_URL
from app.db import engine, Base
from app.videos.api import create_video, get_video, get_all_videos
from app.videos.crud import video_crud


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class VideosTestCase(TestCase):

    def loop(self, function):
        loop = asyncio.get_event_loop()
        try:
            return loop.run_until_complete(function)
        finally:
            pass

    def setUp(self) -> None:
        self.session = AsyncSession(engine)
        self.client = TestClient(app)
        self.user_data = {
            'password': 'test1234',
            'confirm_password': 'test1234',
            'username': 'test',
            'email': 'test@example.com',
            'about': 'string',
            'send_message': True,
        }
        self.category_data = {
            'name': 'FastAPI',
        }
        self.data = {
            'title': 'Anti-YouTube',
            'description': 'Hello world!',
            'category_id': 1,
        }
        self.url = API_V1_URL + '/videos'
        self.loop(create_all())
        os.mkdir(MEDIA_ROOT)

    def tearDown(self) -> None:
        self.loop(self.session.close())
        self.loop(drop_all())
        shutil.rmtree(MEDIA_ROOT)

    def test_videos(self):
        self.client.post(API_V1_URL + '/auth/register', json=self.user_data)
        verification = self.loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(API_V1_URL + '/auth/activate', json={'uuid': verification['uuid']})

        self.loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        self.loop(self.session.commit())

        tokens = self.client.post(API_V1_URL + '/auth/login', data={'username': 'test', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        self.client.post(API_V1_URL + '/categories/', json=self.category_data, headers=headers)

        user = self.loop(user_crud.get(self.session, id=1))

        self.assertEqual(len(self.loop(video_crud.all(self.session))), 0)

        # Create
        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                response = self.loop(
                    create_video(
                        **self.data,
                        video_file=UploadFile(video.name, video, content_type='video/mp4'),
                        preview_file=UploadFile(preview.name, preview, content_type='image/png'),
                        user=user,
                    )
                )
        self.assertEqual(response['category']['name'], 'FastAPI')
        self.assertEqual(response['user']['username'], 'test')
        self.assertEqual(os.path.exists(response['video_file']), True)
        self.assertEqual(os.path.exists(response['preview_file']), True)

        self.assertEqual(len(self.loop(video_crud.all(self.session))), 1)

        with self.assertRaises(HTTPException) as error:
            with open('tests/image.gif', 'rb') as preview:
                with open('tests/test.mp4', 'rb') as video:
                    self.loop(
                        create_video(
                            **self.data,
                            video_file=UploadFile(video.name, video, content_type='video/mp4'),
                            preview_file=UploadFile(preview.name, preview, content_type='image/gif'),
                            user=user,
                        )
                    )

        with self.assertRaises(HTTPException) as error:
            with open('tests/image.png', 'rb') as preview:
                with open('tests/image.png', 'rb') as video:
                    self.loop(
                        create_video(
                            **self.data,
                            video_file=UploadFile(video.name, video, content_type='image/png'),
                            preview_file=UploadFile(preview.name, preview, content_type='image/png'),
                            user=user,
                        )
                    )

        # Create 2 videos for Get all
        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                self.client.post(
                    self.url + '/',
                    headers=headers,
                    data=self.data,
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )
                self.client.post(
                    self.url + '/',
                    headers=headers,
                    data=self.data,
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )

        # Get all

        # Page №1
        response = self.loop(get_all_videos(1))
        self.assertEqual(response['next'], 'http://localhost:8000/api/v1/videos/?page=2')
        self.assertEqual(len(response['results']), 2)
        self.assertEqual(response['results'][0]['id'], 3)
        self.assertEqual(response['results'][1]['id'], 2)
        self.assertEqual(response['previous'], None)

        # Page №2
        response = self.loop(get_all_videos(2))
        self.assertEqual(response['next'], None)
        self.assertEqual(len(response['results']), 1)
        self.assertEqual(response['results'][0]['id'], 1)
        self.assertEqual(response['previous'], 'http://localhost:8000/api/v1/videos/?page=1')

        # Page №3 (error)
        with self.assertRaises(HTTPException) as error:
            self.loop(get_all_videos(3))

        # Get
        response = self.loop(get_video(1))
        self.assertEqual(response['id'], 1)

        with self.assertRaises(HTTPException) as error:
            self.loop(get_video(143))

    def test_videos_request(self):
        self.client.post(API_V1_URL + '/auth/register', json=self.user_data)
        verification = self.loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(API_V1_URL + '/auth/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(API_V1_URL + '/auth/login', data={'username': 'test', 'password': 'test1234'})

        self.loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        self.loop(self.session.commit())

        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        self.client.post(API_V1_URL + '/categories/', json=self.category_data, headers=headers)

        self.assertEqual(len(self.loop(video_crud.all(self.session))), 0)

        # Create
        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                response = self.client.post(
                    self.url + '/',
                    headers=headers,
                    data=self.data,
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['category'], {'id': 1, 'name': 'FastAPI'})
        self.assertEqual(response.json()['user'], {'about': 'string', 'avatar': '', 'id': 1, 'username': 'test'})
        self.assertEqual(os.path.exists(response.json()['video_file']), True)
        self.assertEqual(os.path.exists(response.json()['preview_file']), True)

        self.assertEqual(len(self.loop(video_crud.all(self.session))), 1)

        with open('tests/image.gif', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                response = self.client.post(
                    self.url + '/',
                    headers=headers,
                    data=self.data,
                    files={
                        'preview_file': ('image.gif', preview, 'image/gif'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Preview only format in jpeg or png'})

        with open('tests/image.png', 'rb') as preview:
            with open('tests/image.gif', 'rb') as video:
                response = self.client.post(
                    self.url + '/',
                    headers=headers,
                    data=self.data,
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('image.gif', video, 'image/png'),
                    }
                )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Video only format in mp4'})

        # Create 2 videos for Get all
        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                self.client.post(
                    self.url + '/',
                    headers=headers,
                    data=self.data,
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )
                self.client.post(
                    self.url + '/',
                    headers=headers,
                    data=self.data,
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )

        # Get all

        # Page №1
        response = self.client.get(self.url + '/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['next'], 'http://localhost:8000/api/v1/videos/?page=2')
        self.assertEqual(len(response.json()['results']), 2)
        self.assertEqual(response.json()['results'][0]['id'], 3)
        self.assertEqual(response.json()['results'][1]['id'], 2)
        self.assertEqual(response.json()['previous'], None)

        # Page №2
        response = self.client.get(self.url + '/?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['next'], None)
        self.assertEqual(len(response.json()['results']), 1)
        self.assertEqual(response.json()['results'][0]['id'], 1)
        self.assertEqual(response.json()['previous'], 'http://localhost:8000/api/v1/videos/?page=1')

        # Page №3 (error)
        response = self.client.get(self.url + '/?page=3')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Results not found'})

        # Get
        response = self.client.get(self.url + '/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], 1)

        response = self.client.get(self.url + '/143')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Video not found'})