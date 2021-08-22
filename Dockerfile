FROM python:3.8.10

WORKDIR /site

COPY requirements.txt .

RUN pip install -r requirements.txt && rm -rf /root/.cache/pip

COPY . .

EXPOSE 8000
