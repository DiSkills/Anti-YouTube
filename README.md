# Anti-YouTube: FastAPI

# `Installing`

    create database postgres
    
    create file "config.env" how "config.example.env"

    pip install poetry
    
    poetry install --no-dev

    python main.py


# `Installing Docker (don't working)`

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
