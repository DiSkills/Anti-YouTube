# Anti-YouTube: FastAPI


# `About project`

    YouTube-like video hosting

    Author:
        _Counter021_


#`TODO`
    
    refactor
    
    types in crud
    
    docs paginate
    
    activation in front
    
    send messages for comment
    
    add clear history
    
    search videos
    
    tests comments
    
    export user data, (mb websocket)
    
    tests all requests not (async and database)
    
    add docs in api, docs (check and add when need)
    
    docker script createsuperuser
    
    tests channel
    
    2-authorization (email code) {maybe}
    
    trends, admin, playlists
    
    pagination in categories and history


# `Installing`

    create database postgres
    
    create file "config.env" how "config.example.env"

    pip install poetry
    
    poetry install --no-dev

    python main.py


# `Installing Docker`

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
