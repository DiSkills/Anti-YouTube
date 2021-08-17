import os
import shutil
from unittest import TestCase

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.app import app
from app.auth.crud import verification_crud, user_crud
from app.comments.api import create_comment, get_comments
from app.comments.crud import comment_crud
from app.comments.schemas import CreateComment
from app.config import API_V1_URL, MEDIA_ROOT
from app.db import engine
from tests import create_all, async_loop, drop_all


class CommentTestCase(TestCase):

    def create_user(self, data):
        self.client.post(API_V1_URL + '/auth/register', json=data)
        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(API_V1_URL + '/auth/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(API_V1_URL + '/auth/login', data=data)
        self.headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

    def create_category(self):
        async_loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        async_loop(self.session.commit())
        self.client.post(API_V1_URL + '/categories/', json={'name': 'FastAPI'}, headers=self.headers)

    def create_video(self):
        self.video_data = {
            'title': 'Anti-YouTube',
            'description': 'Hello world!',
            'category_id': 1,
        }

        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                self.client.post(
                    API_V1_URL + '/videos/',
                    headers=self.headers,
                    data=self.video_data,
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )

    def setUp(self) -> None:
        self.session = AsyncSession(engine)
        self.client = TestClient(app)
        self.url = API_V1_URL + '/comments'
        async_loop(create_all())
        os.makedirs(MEDIA_ROOT)

        self.user_data = {
            'password': 'test1234',
            'confirm_password': 'test1234',
            'username': 'test',
            'email': 'test@example.com',
            'about': 'string',
            'send_message': True,
        }
        self.comment_data = {
            "text": "Test",
            "video_id": 1,
            "parent_id": 0
        }

        self.create_user(self.user_data)
        self.create_category()
        self.create_video()

    def tearDown(self) -> None:
        async_loop(self.session.close())
        async_loop(drop_all())
        shutil.rmtree(MEDIA_ROOT)

    def test_comments(self):
        self.assertEqual(len(async_loop(comment_crud.all(self.session))), 0)

        user = async_loop(user_crud.get(self.session, id=1))

        # Create

        response = async_loop(get_comments(1))
        self.assertEqual(response, [])
        self.assertEqual(len(response), 0)

        response = async_loop(create_comment(CreateComment(**self.comment_data), user))
        self.assertEqual(response['is_child'], False)
        self.assertEqual(response['parent'], None)
        self.assertEqual(response['parent_id'], None)

        self.assertEqual(len(async_loop(comment_crud.all(self.session))), 1)

        response = async_loop(create_comment(CreateComment(**{**self.comment_data, 'parent_id': 1}), user))
        self.assertEqual(response['is_child'], True)
        self.assertEqual(response['parent']['id'], 1)
        self.assertEqual(response['parent_id'], 1)
        self.assertEqual(len(async_loop(comment_crud.all(self.session))), 2)

        response = async_loop(create_comment(CreateComment(**{**self.comment_data, 'parent_id': 2}), user))
        self.assertEqual(response['is_child'], True)
        self.assertEqual(response['parent']['id'], 2)
        self.assertEqual(response['parent_id'], 2)
        self.assertEqual(len(async_loop(comment_crud.all(self.session))), 3)

        response = async_loop(create_comment(CreateComment(**self.comment_data), user))
        self.assertEqual(response['is_child'], False)
        self.assertEqual(response['parent'], None)
        self.assertEqual(response['parent_id'], None)
        self.assertEqual(len(async_loop(comment_crud.all(self.session))), 4)

        with self.assertRaises(HTTPException) as error:
            async_loop(create_comment(CreateComment(**{**self.comment_data, 'parent_id': 143}), user))

        with self.assertRaises(HTTPException) as error:
            async_loop(create_comment(CreateComment(**{**self.comment_data, 'video_id': 143}), user))

        # Comments tree

        with self.assertRaises(HTTPException) as error:
            async_loop(get_comments(143))

        response = async_loop(get_comments(1))
        self.assertEqual(len(response), 2)

        self.assertEqual(len(async_loop(comment_crud.all(self.session))), 4)

        tree = response
        self.assertEqual(tree[0]['id'], 4)
        self.assertEqual('children' in tree[0].keys(), False)
        self.assertEqual(tree[1]['id'], 1)
        self.assertEqual(len(tree[1]['children']), 1)
        self.assertEqual(tree[1]['children'][0]['id'], 2)
        self.assertEqual(len(tree[1]['children'][0]['children']), 1)
        self.assertEqual(tree[1]['children'][0]['children'][0]['id'], 3)
        self.assertEqual('children' in tree[1]['children'][0]['children'][0].keys(), False)

        self.create_video()

        response = async_loop(get_comments(2))
        self.assertEqual(response, [])
        self.assertEqual(len(response), 0)

    def test_comments_request(self):
        self.assertEqual(len(async_loop(comment_crud.all(self.session))), 0)

        # Create

        response = self.client.get(self.url + '/video/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        self.assertEqual(len(response.json()), 0)

        response = self.client.post(self.url + '/', json=self.comment_data, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['is_child'], False)
        self.assertEqual(response.json()['parent'], None)
        self.assertEqual(response.json()['parent_id'], None)

        self.assertEqual(len(async_loop(comment_crud.all(self.session))), 1)

        response = self.client.post(self.url + '/', json={**self.comment_data, 'parent_id': 1}, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['is_child'], True)
        self.assertEqual(response.json()['parent']['id'], 1)
        self.assertEqual(response.json()['parent_id'], 1)
        self.assertEqual(len(async_loop(comment_crud.all(self.session))), 2)

        response = self.client.post(self.url + '/', json={**self.comment_data, 'parent_id': 2}, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['is_child'], True)
        self.assertEqual(response.json()['parent']['id'], 2)
        self.assertEqual(response.json()['parent_id'], 2)
        self.assertEqual(len(async_loop(comment_crud.all(self.session))), 3)

        response = self.client.post(self.url + '/', json=self.comment_data, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['is_child'], False)
        self.assertEqual(response.json()['parent'], None)
        self.assertEqual(response.json()['parent_id'], None)
        self.assertEqual(len(async_loop(comment_crud.all(self.session))), 4)

        response = self.client.post(self.url + '/', json={**self.comment_data, 'parent_id': 143}, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Parent not found'})

        response = self.client.post(self.url + '/', json={**self.comment_data, 'video_id': 143}, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Video not found'})

        # Comments tree

        response = self.client.get(self.url + '/video/143')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Video not found'})

        response = self.client.get(self.url + '/video/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

        self.assertEqual(len(async_loop(comment_crud.all(self.session))), 4)

        tree = response.json()
        self.assertEqual(tree[0]['id'], 4)
        self.assertEqual(tree[0]['children'], None)
        self.assertEqual(tree[1]['id'], 1)
        self.assertEqual(len(tree[1]['children']), 1)
        self.assertEqual(tree[1]['children'][0]['id'], 2)
        self.assertEqual(len(tree[1]['children'][0]['children']), 1)
        self.assertEqual(tree[1]['children'][0]['children'][0]['id'], 3)
        self.assertEqual(tree[1]['children'][0]['children'][0]['children'], None)

        self.create_video()

        response = self.client.get(self.url + '/video/2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        self.assertEqual(len(response.json()), 0)
