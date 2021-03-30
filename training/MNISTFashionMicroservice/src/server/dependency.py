import logging
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List, Dict, Optional

from pydantic import BaseSettings, BaseModel, Json
from rq import Queue
import redis as rd


class Settings(BaseSettings):
    ready_to_train = False
    classes: List[str] = []
    num_images: int = 0
    extensions: List[str] = []


class TrainingException(Exception):
    pass

class KerasIdentifierModel(BaseModel):
    class_name: str
    config: Optional[Dict[str,str]]


class ModelData(BaseModel):
    model_structure: str
    loss_function: KerasIdentifierModel
    optimizer: KerasIdentifierModel
    n_epochs: int
    seed: int = 123
    split: float = 0.2
    batch_size: int = 32
    save: bool = False


redis_instance = rd.Redis(host='redis', port=6379)
training_queue = Queue("training", connection=redis_instance)
logger = logging.getLogger("api")
dataset_settings = Settings()

connected = False
shutdown = False
pool = ThreadPoolExecutor(10)
WAIT_TIME = 10
