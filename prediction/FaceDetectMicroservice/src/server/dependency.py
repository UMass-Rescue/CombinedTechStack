from concurrent.futures.thread import ThreadPoolExecutor
import os
from pydantic import BaseSettings
from rq import Queue
import redis as rd
import logging


logger = logging.getLogger("api")

# Redis Queue for model-prediction jobs
redis = rd.Redis(host="redis", port=6379)
prediction_queue = Queue(os.getenv('NAME'), connection=redis)


class Settings(BaseSettings):
    ready_to_predict = False


model_settings = Settings()
image_map = {}


class PredictionException(Exception):
    pass


connected = False
shutdown = False
pool = ThreadPoolExecutor(10)
WAIT_TIME = 10
