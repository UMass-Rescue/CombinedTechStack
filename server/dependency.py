import logging
from concurrent.futures.thread import ThreadPoolExecutor
from enum import Enum
from typing import Optional, List, Dict

from fastapi.security import OAuth2PasswordBearer
from fastapi.security import APIKeyHeader
from passlib.context import CryptContext
from pydantic import BaseModel, BaseSettings, typing, Field
from pymongo import MongoClient
import os

import redis as rd

logger = logging.getLogger("api")

# Pool that tracks the clearing of docker volumes
pool = ThreadPoolExecutor(10)
shutdown = False
WAIT_TIME = 10
redis = rd.Redis(host="redis", port=6379)

# --------------------------------------------------------------------------------
#                                  Database Objects
# --------------------------------------------------------------------------------


client = MongoClient(os.getenv("DB_HOST", default="database"), 27017)
database = client["server_database"]
user_collection = database["users"]  # Create collection for users in database
api_key_collection = database["api_key"]  # Create collection for API keys in database
model_collection = database["models"]  # Create collection for models and their structures in database
training_collection = database["training"]  # Create collection for training status and results
object_collection = database["objects"]  # Create collection for objects in database

PAGINATION_PAGE_SIZE = 15


# --------------------------------------------------------------------------------
#                                  Model Prediction Objects
# --------------------------------------------------------------------------------


class Settings(BaseSettings):
    """
    BaseSettings used to hold available models and datasets for training and prediction.
    """

    available_datasets = {}


settings = Settings()


class AvailableTypes(Enum):
    """
    Object that tracks valid prediction request and model types.
    """
    image = 'image'
    text = 'text'
    video = 'video'
    audio = 'audio'


class UniversalMLPredictionObject(BaseModel):
    """
    Object that is used to store all data associated with a video model prediction request.
    """

    file_names: List[str] = []  # List of all file names that this is uploaded as
    hash_md5: str  # Video md5 hash
    type: AvailableTypes
    users: list = []  # All users who have uploaded the video
    metadata: str = ""  # All video information stored as a string
    models: dict = {}  # ML Model results
    text_content: Optional[str] = '' # Store text for text models
    tags: list = []  # Allow certified user to add tags when video is being uploaded
    user_role_able_to_tag: list = []  # list of users allowed to add and remove tags


class MicroserviceConnection(BaseModel):
    """
    Object that is passed/received via HTTP request when registering a new model or dataset to the server.
    """

    name: str = Field(alias="modelName")
    socket: Optional[str] = Field(alias="modelSocket")
    modelTags: Optional[str] = ''
    modelType: AvailableTypes

    class Config:
        allow_population_by_field_name = True


class ModelPredictionResult(BaseModel):
    model_name: str
    hash: str
    results: dict
    file_type: AvailableTypes  # Enum of available types, as string


class SearchFilter(BaseModel):
    search_filter: dict


# --------------------------------------------------------------------------------
#                             Authentication Objects
# --------------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
api_key_header_auth = APIKeyHeader(name="api_key", auto_error=False)


class ExternalServices(Enum):
    """
    Enum that contains valid external microservices. This enum is used with API keys to ensure that the service
    using an API key is authorized only for specific endpoints.
    """

    predict_microservice = "predict"
    train_microservice = "train"


class Roles(Enum):
    """
    Enum that contains valid role/permission levels. This is used to ensure that users can only access endpoints
    related to the role that they have been assigned.
    """

    admin = "admin"
    investigator = "investigator"
    researcher = "researcher"


class APIKeyData(BaseModel):
    """
    Object that contains information on a registered API key. API keys may only be registered for one microservice
    type and may be disabled at any time.
    """

    key: str
    type: str  # prediction or training
    user: str  # Username of user associated with key
    detail: Optional[str] = ""
    enabled: bool


class Token(BaseModel):
    """
    OAuth2 access token object that is sent via HTTP request.
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Object that stores additional data for an OAuth2 bearer token. The server only tracks username with the token
    since username is a primary key to the user objects collection.
    """

    username: Optional[str] = None


class User(BaseModel):
    """
    Object that stores all data associated with a given user account.
    """

    username: str  # Unique username
    password: str  # Hashed Password, never stored as plaintext
    roles: list
    agency: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False


class CredentialException(Exception):
    """
    Exception raised in main.py when a user does not have access to an endpoint. HTTP 401
    """

    pass

# --------------------------------------------------------------------------------
#                         Dataset + Training Objects
# --------------------------------------------------------------------------------


class LossFunction(BaseModel):
    """
    LossFunction inside HTTP Request body (support only Tensorflow losses)
    """
    class_name: str
    config: Optional[Dict[str, str]]


class OptimizerModel(BaseModel):
    """
    LossFunction inside HTTP Request body (support only Tensorflow losses)
    """
    class_name: List[str]
    learning_rate: Optional[List[float]]
    config: Optional[Dict[str, str]]


class TrainingRequestHttpBody(BaseModel):
    """
    HTTP Request body received from python devtools when creating a training request for a dataset.
    """

    dataset: str
    model_structure: str  # Stringified JSON object of model structure
    loss_function: LossFunction
    optimizer: OptimizerModel
    n_epochs: int
    seed: int = 123
    split: float = 0.2
    batch_size: int = 32
    save_training_results: bool = (
        False  # Whether the results of training is saved to server
    )


class TrainingResult(BaseModel):
    """
    Object that stores all data associated with a single training request.
    """

    dataset: str  # Name of dataset model is being trained on
    training_id: str  # Unique training ID to track job
    username: str  # User associated with this training
    model: TrainingRequestHttpBody  # Details on the model contained in this result
    complete: bool = False  # Whether training result is complete from server
    save: bool = False  # Whether the results of training is saved to server
    training_accuracy: float = -1
    validation_accuracy: float = -1
    training_loss: float = -1
    validation_loss: float = -1
    optimizer_config: str = "{}"
    loss_config: str = "{}"


class TrainingResultHttpBody(BaseModel):
    """
    Response object sent from dataset with training results.
    """

    dataset_name: str
    training_id: str
    results: typing.Any
