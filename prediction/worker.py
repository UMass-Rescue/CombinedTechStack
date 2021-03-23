import os
import uuid
from redis import Redis
from rq import Worker, Queue
from src.model.model import init


redis = Redis(host='redis', port=6379)
queue = Queue(os.getenv('NAME'), connection=redis)

if __name__ == '__main__':
    print('Starting Worker')
    unique_worker_id = str(uuid.uuid4())
    init()  # Ensure that the model is ready to receive predictions.
    print('[Worker] Model Init Complete')
    worker = Worker([queue], connection=redis, name='Worker'+os.getenv('NAME')+'---'+unique_worker_id)
    worker.work()
    print('Ending Worker')
