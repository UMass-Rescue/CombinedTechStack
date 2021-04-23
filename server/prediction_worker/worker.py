import uuid
from redis import Redis
from model.config import model_name
from rq import Queue, SimpleWorker, Connection
from model.model import init, predict
from utility import main
from concurrent.futures.thread import ThreadPoolExecutor


redis = Redis(host='redis', port=6379)
shutdown = False
pool = ThreadPoolExecutor(10)

if __name__ == '__main__':
    print('Starting Worker')
    unique_worker_id = str(uuid.uuid4())
    with Connection(redis):
        queue = Queue(model_name)
        init()  # Ensure that the model is ready to receive predictions.
        pool.submit(main.register_to_server)  # Add this model to the server's list of available models.
        worker = SimpleWorker([queue], connection=redis, name='Worker'+model_name+'---'+unique_worker_id)
        worker.work()
    shutdown = True
    print('Ending Worker')