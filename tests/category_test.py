import asyncio
import os
import shutil
from unittest import TestCase

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.app import app
from app.auth.crud import verification_crud, user_crud
from app.categories.api import create_category, get_category, get_all_categories, update_category, delete_category
from app.categories.crud import category_crud
from app.categories.schemas import CreateCategory, UpdateCategory
from app.config import API_V1_URL, MEDIA_ROOT
from app.db import engine, Base


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class CategoryTestCase(TestCase):

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
        self.loop(create_all())
        os.mkdir(MEDIA_ROOT)

    def tearDown(self) -> None:
        self.loop(self.session.close())
        self.loop(drop_all())
        shutil.rmtree(MEDIA_ROOT)

    def test_categories_request(self):
        self.client.post(API_V1_URL + '/auth/register', json=self.user_data)
        verification = self.loop(verification_crud.get(self.session, user_id=1)).__dict__
        self.client.post(API_V1_URL + '/auth/activate', json={'uuid': verification['uuid']})
        tokens = self.client.post(API_V1_URL + '/auth/login', data={'username': 'test', 'password': 'test1234'})

        self.loop(self.session.execute(update(user_crud.model).filter_by(id=1).values(is_superuser=True)))
        self.loop(self.session.commit())

        headers = {'Authorization': f'Bearer {tokens.json()["access_token"]}'}

        self.assertEqual(len(self.loop(category_crud.all(self.session))), 0)

        # Create
        response = self.client.post(self.url + '/', json=self.data, headers=headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), self.response_data)

        self.assertEqual(len(self.loop(category_crud.all(self.session))), 1)

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

        self.assertEqual(len(self.loop(category_crud.all(self.session))), 0)

        response = self.client.delete(self.url + '/143', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Category not found'})

    def test_categories(self):

        self.assertEqual(len(self.loop(category_crud.all(self.session))), 0)

        # Create
        response = self.loop(create_category(CreateCategory(name=self.data['name'])))
        self.assertEqual(response['id'], 1)
        self.assertEqual(response['name'], self.data['name'])

        self.assertEqual(len(self.loop(category_crud.all(self.session))), 1)

        # Get
        response = self.loop(get_category(1))
        self.assertEqual(response['id'], 1)
        self.assertEqual(response['name'], self.data['name'])

        with self.assertRaises(HTTPException) as error:
            self.loop(get_category(143))

        # Get all
        response = self.loop(get_all_categories())
        self.assertEqual(type(response), list)
        self.assertEqual(response[0]['id'], 1)
        self.assertEqual(response[0]['name'], self.data['name'])

        # Update
        response = self.loop(update_category(1, UpdateCategory(name='Django')))
        self.assertEqual(response['id'], 1)
        self.assertEqual(response['name'], 'Django')

        with self.assertRaises(HTTPException) as error:
            self.loop(update_category(143, UpdateCategory(name='Django')))

        # Delete
        response = self.loop(delete_category(1))
        self.assertEqual(response, {'msg': 'Category has been deleted'})
        self.assertEqual(len(self.loop(category_crud.all(self.session))), 0)

        with self.assertRaises(HTTPException) as error:
            self.loop(delete_category(143))
