CREATE USER video_fastapi WITH PASSWORD 'video';

CREATE DATABASE video_db;
GRANT ALL PRIVILEGES ON DATABASE video_db TO video_fastapi;
