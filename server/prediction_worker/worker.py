import uuid
from redis import Redis

from model.config import model_name, model_type, model_tags
from rq import Queue, SimpleWorker, Connection
from model.model import init, predict


redis = Redis(host='redis', port=6379)

if __name__ == '__main__':
    print('Starting Worker', flush=True)
    unique_worker_id = str(uuid.uuid4())
    with Connection(redis):
        worker_name = 'prediction;' + model_type + ';' + model_name + ';' + model_tags + ';' + unique_worker_id
        queue = Queue(model_name)
        init()  # Ensure that the model is ready to receive predictions.
        worker = SimpleWorker([queue], connection=redis, name=worker_name)
        worker.work()
    print('Ending Worker', flush=True)


