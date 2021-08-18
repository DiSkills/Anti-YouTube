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
from app.db import engine
from app.videos.api import (
    create_video,
    get_video,
    get_all_videos,
    delete_video,
    create_vote,
    update_video,
    search_videos,
)
from app.videos.crud import video_crud, vote_crud, history_crud
from app.videos.schemas import CreateVote
from tests import create_all, drop_all, async_loop


class VideosTestCase(TestCase):

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
        async_loop(create_all())
        os.makedirs(MEDIA_ROOT)

    def tearDown(self) -> None:
        async_loop(self.session.close())
        async_loop(drop_all())
        shutil.rmtree(MEDIA_ROOT)

    def test_videos(self):
        self.client.post(API_V1_URL + '/auth/register', json=self.user_data)
        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(API_V1_URL + '/auth/activate', json={'uuid': verification['uuid']})

        async_loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        async_loop(self.session.commit())

        tokens = self.client.post(API_V1_URL + '/auth/login', data={'username': 'test', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        self.client.post(API_V1_URL + '/categories/', json=self.category_data, headers=headers)

        user = async_loop(user_crud.get(self.session, id=1))

        self.assertEqual(len(async_loop(video_crud.all(self.session))), 0)

        # Create
        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                response = async_loop(
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

        self.assertEqual(len(async_loop(video_crud.all(self.session))), 1)

        with self.assertRaises(HTTPException) as error:
            with open('tests/image.gif', 'rb') as preview:
                with open('tests/test.mp4', 'rb') as video:
                    async_loop(
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
                    async_loop(
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
        response = async_loop(get_all_videos(1))
        self.assertEqual(response['next'], 'http://localhost:8000/api/v1/videos/?page=2')
        self.assertEqual(len(response['results']), 2)
        self.assertEqual(response['results'][0]['id'], 3)
        self.assertEqual(response['results'][1]['id'], 2)
        self.assertEqual(response['previous'], None)

        # Page №2
        response = async_loop(get_all_videos(2))
        self.assertEqual(response['next'], None)
        self.assertEqual(len(response['results']), 1)
        self.assertEqual(response['results'][0]['id'], 1)
        self.assertEqual(response['previous'], 'http://localhost:8000/api/v1/videos/?page=1')

        # Page №3 (error)
        with self.assertRaises(HTTPException) as error:
            async_loop(get_all_videos(3))

        # Get
        response = async_loop(get_video(1))
        self.assertEqual(response['id'], 1)

        with self.assertRaises(HTTPException) as error:
            async_loop(get_video(143))

        # Delete
        video_1 = async_loop(video_crud.get(self.session, id=1))
        self.assertEqual(os.path.exists(video_1.preview_file), True)
        self.assertEqual(os.path.exists(video_1.video_file), True)
        self.assertEqual(len(async_loop(video_crud.all(self.session))), 3)

        response = async_loop(delete_video(1))
        self.assertEqual(response, {'msg': 'Video has been deleted'})

        self.assertEqual(os.path.exists(video_1.preview_file), False)
        self.assertEqual(os.path.exists(video_1.video_file), False)

        self.assertEqual(len(async_loop(video_crud.all(self.session))), 2)

        with self.assertRaises(HTTPException) as error:
            async_loop(delete_video(1))

        # Create vote
        self.assertEqual(len(async_loop(vote_crud.all(self.session))), 0)
        response = self.client.get(self.url + '/2')
        self.assertEqual(response.json()['votes'], {'dislikes': 0, 'likes': 0})

        response = async_loop(create_vote(CreateVote(vote=1, video_id=2), user))
        self.assertEqual(response['id'], 2)
        self.assertEqual(response['votes'], {'dislikes': 0, 'likes': 1})

        self.assertEqual(len(async_loop(vote_crud.all(self.session))), 1)
        response = self.client.get(self.url + '/2')
        self.assertEqual(response.json()['votes'], {'dislikes': 0, 'likes': 1})

        response = self.client.get(self.url + '/3')
        self.assertEqual(response.json()['votes'], {'dislikes': 0, 'likes': 0})

        with self.assertRaises(HTTPException) as error:
            async_loop(create_vote(CreateVote(vote=1, video_id=2), user))

        with self.assertRaises(HTTPException) as error:
            async_loop(create_vote(CreateVote(vote=1, video_id=143), user))

        with self.assertRaises(ValueError) as error:
            async_loop(create_vote(CreateVote(vote=35, video_id=2), user))

        with self.assertRaises(ValueError) as error:
            async_loop(create_vote(CreateVote(vote=-23, video_id=2), user))

        response = async_loop(create_vote(CreateVote(vote=0, video_id=3), user))
        self.assertEqual(response['id'], 3)
        self.assertEqual(response['votes'], {'dislikes': 1, 'likes': 0})
        self.assertEqual(len(async_loop(vote_crud.all(self.session))), 2)

        # 2 user
        self.client.post(API_V1_URL + '/auth/register', json={**self.user_data, 'username': 'test2', 'email': 'test@exapmple.com'})
        verification = async_loop(verification_crud.get(self.session, user_id=2)).__dict__
        self.client.post(API_V1_URL + '/auth/activate', json={'uuid': verification['uuid']})

        user_2 = async_loop(user_crud.get(self.session, id=2))

        response = async_loop(create_vote(CreateVote(vote=1, video_id=2), user_2))
        self.assertEqual(response['votes'], {'dislikes': 0, 'likes': 2})

        self.assertEqual(len(async_loop(vote_crud.all(self.session))), 3)

        response = async_loop(create_vote(CreateVote(vote=1, video_id=3), user_2))

        self.assertEqual(response['votes'], {'dislikes': 1, 'likes': 1})

        self.assertEqual(len(async_loop(vote_crud.all(self.session))), 4)

        # Update video
        video_3 = async_loop(video_crud.get(self.session, id=3))
        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                response = async_loop(
                    update_video(
                        pk=3,
                        **{**self.data, 'title': 'Test'},
                        video_file=UploadFile(video.name, video, content_type='video/mp4'),
                        preview_file=UploadFile(preview.name, preview, content_type='image/png'),
                        user=user,
                    )
                )
        self.assertEqual(response['id'], 3)
        self.assertNotEqual(response['title'], video_3.title)
        self.assertNotEqual(response['video_file'], video_3.video_file)
        self.assertNotEqual(response['preview_file'], video_3.preview_file)

        self.assertEqual(os.path.exists(video_3.preview_file), False)
        self.assertEqual(os.path.exists(video_3.video_file), False)

        self.assertEqual(os.path.exists(response['preview_file']), True)
        self.assertEqual(os.path.exists(response['video_file']), True)

        with self.assertRaises(HTTPException) as error:
            with open('tests/image.png', 'rb') as preview:
                with open('tests/test.mp4', 'rb') as video:
                    async_loop(
                        update_video(
                            pk=143,
                            **{**self.data, 'title': 'Test'},
                            video_file=UploadFile(video.name, video, content_type='video/mp4'),
                            preview_file=UploadFile(preview.name, preview, content_type='image/png'),
                            user=user,
                        )
                    )

        self.client.post(
            API_V1_URL + '/auth/register', json={**self.user_data, 'username': 'Test', 'email': 'Test@example.com'}
        )
        verification = async_loop(verification_crud.get(self.session, user_id=3)).__dict__
        self.client.post(API_V1_URL + '/auth/activate', json={'uuid': verification['uuid']})
        user_3 = async_loop(user_crud.get(self.session, id=3))
        with self.assertRaises(HTTPException) as error:
            with open('tests/image.png', 'rb') as preview:
                with open('tests/test.mp4', 'rb') as video:
                    async_loop(
                        update_video(
                            pk=3,
                            **{**self.data, 'title': 'Test'},
                            video_file=UploadFile(video.name, video, content_type='video/mp4'),
                            preview_file=UploadFile(preview.name, preview, content_type='image/png'),
                            user=user_3,
                        )
                    )

        async_loop(self.session.execute(update(user_crud.model).filter_by(id=3).values(is_superuser=True)))
        async_loop(self.session.commit())
        user_3 = async_loop(user_crud.get(self.session, id=3))

        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                response = async_loop(
                    update_video(
                        pk=3,
                        **{**self.data, 'title': 'Anti-YouTube 2'},
                        video_file=UploadFile(video.name, video, content_type='video/mp4'),
                        preview_file=UploadFile(preview.name, preview, content_type='image/png'),
                        user=user_3,
                    )
                )
        self.assertEqual(response['title'], 'Anti-YouTube 2')

        response = async_loop(search_videos('2'))
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['id'], 3)

        response = async_loop(search_videos('anti'))
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0]['id'], 3)
        self.assertEqual(response[1]['id'], 2)

        response = async_loop(search_videos('example'))
        self.assertEqual(len(response), 0)

    def test_videos_request(self):
        self.client.post(API_V1_URL + '/auth/register', json=self.user_data)
        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(API_V1_URL + '/auth/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(API_V1_URL + '/auth/login', data={'username': 'test', 'password': 'test1234'})

        async_loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        async_loop(self.session.commit())

        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        self.client.post(API_V1_URL + '/categories/', json=self.category_data, headers=headers)

        self.assertEqual(len(async_loop(video_crud.all(self.session))), 0)

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

        self.assertEqual(len(async_loop(video_crud.all(self.session))), 1)

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

        # Delete
        video_1 = async_loop(video_crud.get(self.session, id=1))
        self.assertEqual(os.path.exists(video_1.preview_file), True)
        self.assertEqual(os.path.exists(video_1.video_file), True)

        async_loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        async_loop(self.session.commit())
        self.assertEqual(len(async_loop(video_crud.all(self.session))), 3)

        response = self.client.delete(self.url + '/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'msg': 'Video has been deleted'})

        self.assertEqual(os.path.exists(video_1.preview_file), False)
        self.assertEqual(os.path.exists(video_1.video_file), False)

        self.assertEqual(len(async_loop(video_crud.all(self.session))), 2)

        response = self.client.delete(self.url + '/1', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Video not found'})

        # Streaming video
        response = self.client.get(self.url + '/video/2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers, {'content-type': 'video/mp4', 'accept-ranges': 'bytes', 'content-length': '0'}
        )

        response = self.client.get(self.url + '/video/2', headers={'range': 'bytes=100-'})
        self.assertEqual(response.status_code, 206)

        response = self.client.get(self.url + '/video/143')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Video not found'})

        # Create vote
        self.assertEqual(len(async_loop(vote_crud.all(self.session))), 0)
        response = self.client.get(self.url + '/2')
        self.assertEqual(response.json()['votes'], {'dislikes': 0, 'likes': 0})

        response = self.client.post(self.url + '/vote', headers=headers, json={'vote': 1, 'video_id': 2})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['id'], 2)
        self.assertEqual(response.json()['votes'], {'dislikes': 0, 'likes': 1})

        self.assertEqual(len(async_loop(vote_crud.all(self.session))), 1)
        response = self.client.get(self.url + '/2')
        self.assertEqual(response.json()['votes'], {'dislikes': 0, 'likes': 1})

        response = self.client.get(self.url + '/3')
        self.assertEqual(response.json()['votes'], {'dislikes': 0, 'likes': 0})

        response = self.client.post(self.url + '/vote', headers=headers, json={'vote': 1, 'video_id': 2})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Vote exist'})

        self.assertEqual(len(async_loop(vote_crud.all(self.session))), 1)
        response = self.client.get(self.url + '/2')
        self.assertEqual(response.json()['votes'], {'dislikes': 0, 'likes': 1})

        response = self.client.post(self.url + '/vote', headers=headers, json={'vote': 1, 'video_id': 143})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Video not found'})

        response = self.client.post(self.url + '/vote', headers=headers, json={'vote': 35, 'video_id': 2})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['detail'][0]['msg'], 'Vote is 0 (dislike) or 1 (like)')

        response = self.client.post(self.url + '/vote', headers=headers, json={'vote': -23, 'video_id': 2})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['detail'][0]['msg'], 'Vote is 0 (dislike) or 1 (like)')

        self.assertEqual(len(async_loop(vote_crud.all(self.session))), 1)

        response = self.client.post(self.url + '/vote', headers=headers, json={'vote': 0, 'video_id': 3})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['id'], 3)
        self.assertEqual(response.json()['votes'], {'dislikes': 1, 'likes': 0})

        self.assertEqual(len(async_loop(vote_crud.all(self.session))), 2)

        # 2 user
        self.client.post(API_V1_URL + '/auth/register', json={**self.user_data, 'username': 'test2', 'email': 'test@exapmple.com'})
        verification = async_loop(verification_crud.get(self.session, user_id=2)).__dict__
        self.client.post(API_V1_URL + '/auth/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(API_V1_URL + '/auth/login', data={'username': 'test2', 'password': 'test1234'})

        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

        response = self.client.post(self.url + '/vote', headers=headers, json={'vote': 1, 'video_id': 2})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['votes'], {'dislikes': 0, 'likes': 2})

        self.assertEqual(len(async_loop(vote_crud.all(self.session))), 3)

        response = self.client.post(self.url + '/vote', headers=headers, json={'vote': 1, 'video_id': 3})
        self.assertEqual(response.status_code, 201)

        self.assertEqual(response.json()['votes'], {'dislikes': 1, 'likes': 1})

        self.assertEqual(len(async_loop(vote_crud.all(self.session))), 4)

        # History add
        self.assertEqual(len(async_loop(history_crud.all(self.session))), 0)
        self.assertEqual(async_loop(video_crud.get(self.session, id=2)).views, 0)

        response = self.client.post(self.url + '/add-to-history?pk=2', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'msg': 'Add to history and new view'})

        self.assertEqual(len(async_loop(history_crud.all(self.session))), 1)
        self.assertEqual(async_loop(video_crud.get(self.session, id=2)).views, 1)

        response = self.client.post(self.url + '/add-to-history?pk=143', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Video not found'})

        self.assertEqual(async_loop(video_crud.get(self.session, id=3)).views, 0)

        self.client.post(self.url + '/add-to-history?pk=3', headers=headers)
        self.assertEqual(len(async_loop(history_crud.all(self.session))), 2)
        self.assertEqual(async_loop(video_crud.get(self.session, id=2)).views, 1)
        self.assertEqual(async_loop(video_crud.get(self.session, id=3)).views, 1)

        # History get
        response = self.client.get(API_V1_URL + '/auth/history', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]['id'], 3)
        self.assertEqual(response.json()[1]['id'], 2)

        # New view
        response = self.client.post(self.url + '/add-to-history?pk=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'msg': 'New view'})
        self.assertEqual(async_loop(video_crud.get(self.session, id=2)).views, 2)
        self.assertEqual(len(async_loop(history_crud.all(self.session))), 2)

        # Clear history

        tokens = self.client.post(API_V1_URL + '/auth/login', data={'username': 'test', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        self.client.post(self.url + '/add-to-history?pk=2', headers=headers)

        tokens = self.client.post(API_V1_URL + '/auth/login', data={'username': 'test2', 'password': 'test1234'})

        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

        self.assertEqual(len(async_loop(history_crud.all(self.session))), 3)
        response = self.client.delete(self.url + '/history/clear', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'msg': 'History cleared'})
        self.assertEqual(len(async_loop(history_crud.all(self.session))), 1)

        # Update video
        video_3 = async_loop(video_crud.get(self.session, id=3))
        tokens = self.client.post(API_V1_URL + '/auth/login', data={'username': 'test', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                response = self.client.put(
                    self.url + '/3',
                    headers=headers,
                    data={**self.data, 'title': 'Test'},
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], 3)
        self.assertNotEqual(response.json()['title'], video_3.title)
        self.assertNotEqual(response.json()['video_file'], video_3.video_file)
        self.assertNotEqual(response.json()['preview_file'], video_3.preview_file)

        self.assertEqual(os.path.exists(video_3.preview_file), False)
        self.assertEqual(os.path.exists(video_3.video_file), False)

        self.assertEqual(os.path.exists(response.json()['preview_file']), True)
        self.assertEqual(os.path.exists(response.json()['video_file']), True)

        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                response = self.client.put(
                    self.url + '/143',
                    headers=headers,
                    data={**self.data, 'title': 'Test'},
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Video not found'})

        self.client.post(
            API_V1_URL + '/auth/register', json={**self.user_data, 'username': 'Test', 'email': 'Test@example.com'}
        )
        verification = async_loop(verification_crud.get(self.session, user_id=3)).__dict__
        self.client.post(API_V1_URL + '/auth/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(API_V1_URL + '/auth/login', data={'username': 'Test', 'password': 'test1234'})
        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                response = self.client.put(
                    self.url + '/3',
                    headers=headers,
                    data={**self.data, 'title': 'Test'},
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {'detail': 'You not published this video'})

        async_loop(self.session.execute(update(user_crud.model).filter_by(id=3).values(is_superuser=True)))
        async_loop(self.session.commit())

        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                response = self.client.put(
                    self.url + '/3',
                    headers=headers,
                    data={**self.data, 'title': 'Anti-YouTube 2'},
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Anti-YouTube 2')

        response = self.client.get(self.url + '/search?q=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['id'], 3)

        response = self.client.get(self.url + '/search?q=anti')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]['id'], 3)
        self.assertEqual(response.json()[1]['id'], 2)

        response = self.client.get(self.url + '/search?q=example')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)
