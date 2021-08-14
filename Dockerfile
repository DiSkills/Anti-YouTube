FROM python:3.8.10

WORKDIR /site

COPY poetry.lock .
COPY pyproject.toml .
COPY entrypoint.sh .

RUN pip install poetry

RUN poetry export -f requirements.txt --output requirements.txt

RUN pip install -r requirements.txt

RUN chmod +x entrypoint.sh

COPY . .

ENTRYPOINT ["sh", "/site/entrypoint.sh"]
