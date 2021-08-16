FROM python:3.8.10

RUN apt-get update && apt-get install --no-install-recommends -y curl build-essential

RUN pip install poetry

WORKDIR /site

COPY poetry.lock .
COPY pyproject.toml .

RUN poetry install --no-dev

COPY . .

CMD ["poetry", "run", "uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
