from dotenv import load_dotenv

import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, 'config.env'))

API_V1_URL = r'/api/v1'

PROJECT_NAME = 'Video'
SERVER_HOST_FRONT_END = 'http://localhost:3000'
SERVER_HOST = 'http://localhost:8000'

SECRET_KEY = os.environ.get('SECRET_KEY')

PAGINATE_SIZE = 3

BACKEND_CORS_ORIGINS = [
    'http://localhost',
    'http://localhost:8000',
]

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 15

TESTS = int(os.environ.get('TESTS'))

POSTGRES_USER = os.environ.get('POSTGRES_USER')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
POSTGRES_SERVER = os.environ.get('POSTGRES_SERVER')
POSTGRES_DB = os.environ.get('POSTGRES_DB')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT')

DATABASE_URL = f'postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}'
MEDIA_ROOT = 'media/'

if TESTS:
    DATABASE_URL = f'postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}_test'
    MEDIA_ROOT = 'media/tests/'
    PAGINATE_SIZE = 2

SMTP_TLS = True
SMTP_PORT = 587
SMTP_HOST = 'smtp.googlemail.com'
EMAILS_FROM_EMAIL = 'robot@counter.com'
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

EMAILS_FROM_NAME = PROJECT_NAME
EMAIL_RESET_TOKEN_EXPIRE_HOURS = 48
EMAIL_TEMPLATES_DIR = r'email-templates/build'
EMAILS_ENABLED = SMTP_HOST and SMTP_PORT and EMAILS_FROM_EMAIL
