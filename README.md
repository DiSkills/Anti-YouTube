# Anti-YouTube: FastAPI

<div style="text-align:center">
  <img alt="Anti-YouTube: FastAPI" src="https://github.com/Counter0021/Anti-YouTube-front-end/blob/logo/public/logo512.png?raw=true">
</div>

## Technology stack
![Python percent](https://img.shields.io/github/languages/top/Counter0021/Anti-YouTube-back-end.svg)
![Python version](https://img.shields.io/badge/python-3.8.10-green)
![API version](https://img.shields.io/badge/API-v0.3.3-orange)
![tests](https://img.shields.io/badge/tests-passing-success)
![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)

### `Back-end`
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/fastapi-109989?style=for-the-badge&logo=FASTAPI&logoColor=white)
![SqlAlchemy](https://img.shields.io/badge/-SqlAlchemy-FCA121?style=for-the-badge&logo=SqlAlchemy)
![Celery](https://img.shields.io/badge/-Celery-%2300C7B7?style=for-the-badge&logo=Celery)
![Redis](https://img.shields.io/badge/-Redis-FCA121?style=for-the-badge&logo=Redis)
![Swagger](https://img.shields.io/badge/Swagger-85EA2D?style=for-the-badge&logo=Swagger&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)

### `Tools`
![PyCharm](https://img.shields.io/badge/pycharm-143?style=for-the-badge&logo=pycharm&logoColor=black&color=black&labelColor=green)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)
![Firefox](https://img.shields.io/badge/Firefox_Browser-FF7139?style=for-the-badge&logo=Firefox-Browser&logoColor=white)
![Docker](https://img.shields.io/badge/-Docker-46a2f1?style=for-the-badge&logo=docker&logoColor=white)
![Postman](https://img.shields.io/badge/Postman-FCA121?style=for-the-badge&logo=postman)
![Git](https://img.shields.io/badge/-Git-black?style=for-the-badge&logo=git)
![GitHub](https://img.shields.io/badge/-GitHub-181717?style=for-the-badge&logo=github)
![NGINX](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)

## TODO
- [ ] Back-end
  - [ ] Auth
      - [x] Register
      - [x] Activate
      - [x] Login
      - [X] Refresh token
      - [x] Follow
      - [x] Unfollow
      - [x] Reset password
      - [x] Get username on email
      - [x] Change data
      - [x] Change password
      - [x] Avatar
      - [x] Channel
      - [x] History
      - [x] Subscriptions
      - [x] 2-step auth
      - [x] Google auth
      - [x] Celery send email
      - [ ] Feedbacks
      - [ ] Block video
      - [ ] Export user data (websocket and celery)
  - [x] Categories
    - [x] Get all
    - [x] Get
    - [x] Change
    - [x] Delete
  - [x] Videos
    - [x] Media
    - [x] Trends
    - [x] Search
    - [x] Create
    - [x] Get all with pagination
    - [x] Get
    - [x] Delete
    - [x] Update video
    - [x] Streaming video
    - [x] Vote (likes and dislikes)
    - [x] Add to history
    - [x] Clear history
  - [x] Comments tree
    - [x] Create comments
    - [x] Get comments
    - [x] Send email about new comment
- [x] Deploy
  - [x] Docker


## `Installing`

    Need front-end: https://github.com/Counter0021/Anti-YouTube-front-end

    create file "config.docker.env" how "config.docker.example.env"

    Build:
        docker-compose build

    Up:
        docker-compose up

    Build and up:
        docker-compose up --build

    if port 5432 listen:
        sudo service postgresql stop
    
    if need delete images for docker:
        docker system prune -a
