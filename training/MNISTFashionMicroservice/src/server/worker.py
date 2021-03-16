from dependency import redis_instance, training_queue
from rq import Worker

if __name__ == '__main__':
    print('Starting Worker')
    worker = Worker([training_queue], connection=redis_instance, name='training_worker')
    worker.work()
    print('Ending Worker')
