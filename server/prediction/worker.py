import uuid
from redis import Redis
from model.info import model_name
from rq import Queue, Worker, Connection
from model.model import init
from utility import main


redis = Redis(host='redis', port=6379)

if __name__ == '__main__':
    print('Starting Worker')
    unique_worker_id = str(uuid.uuid4())
    init()  # Ensure that the model is ready to receive predictions.
    registration_result = main.register_to_server()  # Add this model to the server's list of available models.
    print('[Worker] ' + registration_result)
    print('[Worker] Model Init Complete')
    with Connection(redis):
        queue = Queue(model_name)
        worker = Worker([queue], connection=redis, name='Worker'+model_name+'---'+unique_worker_id)
        worker.work()
    print('Ending Worker')

