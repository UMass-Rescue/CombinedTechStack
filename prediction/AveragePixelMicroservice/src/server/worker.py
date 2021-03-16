import os

from redis import Redis
from rq import Worker, Queue
from src.model.model import init
from src.server.dependency import model_settings

redis = Redis(host='redis', port=6379)
queue = Queue(os.getenv('NAME'), connection=redis)

if __name__ == '__main__':
    print('Starting Worker')
    init()
    model_settings.ready_to_predict = True
    print('[Worker] Model Init Complete')
    worker = Worker([queue], connection=redis, name='Worker'+os.getenv('NAME'))
    worker.work()
    print('Ending Worker')
