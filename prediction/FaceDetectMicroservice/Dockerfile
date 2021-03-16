FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

WORKDIR /app

COPY . /app

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

RUN pip --no-cache-dir install -r requirements.txt