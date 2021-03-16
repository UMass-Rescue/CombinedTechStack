import json

from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware

import uuid
import time

from starlette.responses import JSONResponse

from dotenv import load_dotenv
import os

from src.server import dependency
from src.server.dependency import dataset_settings, TrainingException, pool, logger, ModelData, training_queue
from src.server.server_connection import register_model_to_server
from src.server.training import train_model
from src.server.utility import setup_dataset

app = FastAPI()

# Must have CORSMiddleware to enable localhost client and server
origins = [
    "http://localhost",
    "http://host.docker.internal",
    "http://host.docker.internal:5000",
    "http://localhost:3000",
    "http://localhost:5057",
    "http://localhost:5000",
    "http://localhost:6381",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(TrainingException)
async def prediction_exception_handler(request: Request, exc: TrainingException):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": 'failure',
            "detail": "Dataset is not ready to train models."
        },
    )


@app.get("/")
async def root():
    """
    Default endpoint for testing if the server is running
    :return: Positive JSON Message
    """
    return {"MLDatasetTemplate is Running!"}


@app.on_event("startup")
def initial_startup():
    """
    Calls the init() method in the training and prepares the training to receive predictions. The init
    task may take a long time to complete, so the settings field ready_to_predict will be updated
    asynchronously when init() completes. This will also begin the background registration task
    to the server.

    :return: {"status": "success"} upon startup completion. No guarantee that init() is done processing.
    """
    # Run startup task async
    load_dotenv()

    # Register the training to the server in a separate thread to avoid meddling with
    # initializing the service which might be used directly by other client later on
    # We will only run the registration once the training init is complete.
    def init_dataset_helper():
        logger.debug('Beginning Dataset Initialization Process.')
        setup_dataset()
        dataset_settings.ready_to_train = True
        logger.debug('Finishing Dataset Initialization Process.')
        pool.submit(register_model_to_server, os.getenv('SERVER_PORT'), os.getenv('PORT'), os.getenv('DATASET_NAME'))

    pool.submit(init_dataset_helper)
    return {"status": "success", 'detail': 'server startup in progress'}


@app.on_event('shutdown')
def on_shutdown():
    dataset_settings.ready_to_train = False

    dependency.shutdown = True  # Send shutdown signal to threads
    pool.shutdown()  # Clear any non-processed jobs from thread queue

    return {
        'status': 'success',
        'detail': 'Deregister complete and server shutting down.',
    }


@app.get("/status")
async def check_status():
    """
    Checks the current training status of the dataset. Models are not able to be trained
    until this method returns {"result": "True"}.

    :return: {"result": "True"} if dataset is ready for training models, else {"result": "False"}
    """

    if not dataset_settings.ready_to_train:
        raise TrainingException()

    return {
        'status': 'success',
        'detail': 'Dataset ready to receive model training requests.'
    }


@app.get('/detail')
async def get_dataset_details():
    if not dataset_settings.ready_to_train:
        raise TrainingException()

    return {
        'num_images': dataset_settings.num_images,
        'extensions': dataset_settings.extensions,
        'classes': dataset_settings.classes,
    }


@app.post("/train")
async def start_model_training(model_data: ModelData):
    """
    Begins the training process for a model on this dataset. This method must be called after the init() method
    has run at least once, otherwise this will fail with a HTTP Error. The input is a python file that contains the
    training code for the model

    :param model_data: Python file object containing model code to run for training
    :return: JSON indicating training initiation success/failure and the job ID
    """

    # Ensure training is ready to receive prediction requests
    if not dataset_settings.ready_to_train:
        raise TrainingException()

    training_id = str(uuid.uuid4())

    training_queue.enqueue(train_model, training_id, model_data, job_id=training_id)

    return {
        'status': 'success',
        'detail': 'Job has been enqueued and is pending',
        "id": training_id,
    }



