FROM python:3.8.10

RUN pip install poetry

WORKDIR /site

COPY poetry.lock .
COPY pyproject.toml .

RUN poetry install --no-dev

COPY . .

EXPOSE 8000
