import uuid
from redis import Redis
from model.info import model_name
from rq import Worker, Queue
from model.model import init

redis = Redis(host='redis', port=6379)
queue = Queue(model_name, connection=redis)

if __name__ == '__main__':
    print('Starting Worker')
    unique_worker_id = str(uuid.uuid4())
    init()  # Ensure that the model is ready to receive predictions.
    print('[Worker] Model Init Complete')
    worker = Worker([queue], connection=redis, name='Worker'+model_name+'---'+unique_worker_id)
    worker.work()
    print('Ending Worker')