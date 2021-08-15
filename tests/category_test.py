import os
import shutil
from unittest import TestCase

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.app import app
from app.auth.crud import verification_crud, user_crud
from app.categories.api import (
    create_category,
    get_category,
    get_all_categories,
    update_category,
    delete_category,
    get_videos_for_category,
)
from app.categories.crud import category_crud
from app.categories.schemas import CreateCategory, UpdateCategory
from app.config import API_V1_URL, MEDIA_ROOT
from app.db import engine
from tests import create_all, drop_all, async_loop


class CategoryTestCase(TestCase):

    def setUp(self) -> None:
        self.session = AsyncSession(engine)
        self.client = TestClient(app)
        self.user_data = {
            'password': 'test1234',
            'confirm_password': 'test1234',
            'username': 'test',
            'email': 'test@example.com',
            'about': 'string',
            'send_message': True
        }
        self.data = {
            'name': 'FastAPI',
        }
        self.response_data = {
            'name': 'FastAPI',
            'id': 1,
        }
        self.url = API_V1_URL + '/categories'
        async_loop(create_all())
        os.mkdir(MEDIA_ROOT)

    def tearDown(self) -> None:
        async_loop(self.session.close())
        async_loop(drop_all())
        shutil.rmtree(MEDIA_ROOT)

    def test_categories_videos(self):
        self.client.post(API_V1_URL + '/auth/register', json=self.user_data)
        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(API_V1_URL + '/auth/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(API_V1_URL + '/auth/login', data={'username': 'test', 'password': 'test1234'})

        async_loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        async_loop(self.session.commit())

        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        self.client.post(self.url + '/', json=self.data, headers=headers)
        self.client.post(self.url + '/', json={'name': 'Django'}, headers=headers)

        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                self.client.post(
                    API_V1_URL + '/videos/',
                    headers=headers,
                    data={
                        'title': 'Anti-YouTube',
                        'description': 'Hello world!',
                        'category_id': 1,
                    },
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )

                self.client.post(
                    API_V1_URL + '/videos/',
                    headers=headers,
                    data={
                        'title': 'Anti-YouTube',
                        'description': 'Hello world!',
                        'category_id': 2,
                    },
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )

        response = async_loop(get_videos_for_category(1))
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['id'], 1)

        response = async_loop(get_videos_for_category(2))
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['id'], 2)

        with self.assertRaises(HTTPException) as error:
            async_loop(get_videos_for_category(143))

    def test_categories_videos_request(self):
        self.client.post(API_V1_URL + '/auth/register', json=self.user_data)
        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(API_V1_URL + '/auth/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(API_V1_URL + '/auth/login', data={'username': 'test', 'password': 'test1234'})

        async_loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        async_loop(self.session.commit())

        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}
        self.client.post(self.url + '/', json=self.data, headers=headers)
        self.client.post(self.url + '/', json={'name': 'Django'}, headers=headers)

        with open('tests/image.png', 'rb') as preview:
            with open('tests/test.mp4', 'rb') as video:
                self.client.post(
                    API_V1_URL + '/videos/',
                    headers=headers,
                    data={
                        'title': 'Anti-YouTube',
                        'description': 'Hello world!',
                        'category_id': 1,
                    },
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )

                self.client.post(
                    API_V1_URL + '/videos/',
                    headers=headers,
                    data={
                        'title': 'Anti-YouTube',
                        'description': 'Hello world!',
                        'category_id': 2,
                    },
                    files={
                        'preview_file': ('image.png', preview, 'image/png'),
                        'video_file': ('test.mp4', video, 'video/mp4'),
                    }
                )

        response = self.client.get(self.url + '/videos/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['id'], 1)

        response = self.client.get(self.url + '/videos/2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['id'], 2)

        response = self.client.get(self.url + '/videos/143')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Category not found'})

    def test_categories_request(self):
        self.client.post(API_V1_URL + '/auth/register', json=self.user_data)
        verification = async_loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(API_V1_URL + '/auth/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(API_V1_URL + '/auth/login', data={'username': 'test', 'password': 'test1234'})

        async_loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        async_loop(self.session.commit())

        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

        self.assertEqual(len(async_loop(category_crud.all(self.session))), 0)

        # Create
        response = self.client.post(self.url + '/', json=self.data, headers=headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), self.response_data)

        self.assertEqual(len(async_loop(category_crud.all(self.session))), 1)

        # Get
        response = self.client.get(self.url + '/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.response_data)

        response = self.client.get(self.url + '/143')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Category not found'})

        # Get all
        response = self.client.get(self.url + '/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [self.response_data])

        # Update
        response = self.client.put(self.url + '/1', json={'name': 'Django'}, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'name': 'Django', 'id': 1})

        response = self.client.put(self.url + '/143', json={'name': 'Django'}, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Category not found'})

        # Delete
        response = self.client.delete(self.url + '/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'msg': 'Category has been deleted'})

        self.assertEqual(len(async_loop(category_crud.all(self.session))), 0)

        response = self.client.delete(self.url + '/143', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Category not found'})

    def test_categories(self):

        self.assertEqual(len(async_loop(category_crud.all(self.session))), 0)

        # Create
        response = async_loop(create_category(CreateCategory(name=self.data['name'])))
        self.assertEqual(response['id'], 1)
        self.assertEqual(response['name'], self.data['name'])

        self.assertEqual(len(async_loop(category_crud.all(self.session))), 1)

        # Get
        response = async_loop(get_category(1))
        self.assertEqual(response['id'], 1)
        self.assertEqual(response['name'], self.data['name'])

        with self.assertRaises(HTTPException) as error:
            async_loop(get_category(143))

        # Get all
        response = async_loop(get_all_categories())
        self.assertEqual(type(response), list)
        self.assertEqual(response[0]['id'], 1)
        self.assertEqual(response[0]['name'], self.data['name'])

        # Update
        response = async_loop(update_category(1, UpdateCategory(name='Django')))
        self.assertEqual(response['id'], 1)
        self.assertEqual(response['name'], 'Django')

        with self.assertRaises(HTTPException) as error:
            async_loop(update_category(143, UpdateCategory(name='Django')))

        # Delete
        response = async_loop(delete_category(1))
        self.assertEqual(response, {'msg': 'Category has been deleted'})
        self.assertEqual(len(async_loop(category_crud.all(self.session))), 0)

        with self.assertRaises(HTTPException) as error:
            async_loop(delete_category(143))
