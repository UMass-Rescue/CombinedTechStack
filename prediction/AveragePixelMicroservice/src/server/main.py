import base64
import logging
import os

import requests
from secrets import API_KEY
from fastapi import File, UploadFile, FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from src.model.model import predict, init
from src.server import dependency
from src.server.dependency import model_settings, PredictionException, pool, redis
from src.server.server_connection import register_model_to_server
from starlette.responses import JSONResponse

app = FastAPI()

# Must have CORSMiddleware to enable localhost client and server
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5057",
    "http://localhost:5000",
    "http://localhost:6379",
]

logger = logging.getLogger("api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(PredictionException)
async def prediction_exception_handler(request: Request, exc: PredictionException):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": 'failure',
            "detail": "Model is not ready to receive predictions."
        },
    )


@app.get("/")
async def root():
    """
    Default endpoint for testing if the server is running
    :return: Positive JSON Message
    """
    return {"MLMicroserviceTemplate is Running!"}


@app.on_event("startup")
def initial_startup():
    """
    Calls the init() method in the model and prepares the model to receive predictions. The init
    task may take a long time to complete, so the settings field ready_to_predict will be updated
    asynchronously when init() completes. This will also begin the background registration task
    to the server.

    :return: {"status": "success"} upon startup completion. No guarantee that init() is done processing.
    """

    # Register the model to the server in a separate thread to avoid meddling with
    # initializing the service which might be used directly by other client later on
    # We will only run the registration once the model init is complete.
    def init_model_helper():
        logger.debug('Beginning Model Initialization Process.')
        init()
        model_settings.ready_to_predict = True
        logger.debug('Finishing Model Initialization Process.')
        pool.submit(register_model_to_server, os.getenv('SERVER_PORT'), os.getenv('PORT'), os.getenv('NAME'), os.getenv("MODEL_NAME"), os.getenv("MODEL_TAGS"))

    pool.submit(init_model_helper)
    return {"status": "success", 'detail': 'server startup in progress'}


@app.on_event('shutdown')
def on_shutdown():
    model_settings.ready_to_predict = False

    dependency.shutdown = True  # Send shutdown signal to threads
    pool.shutdown()  # Clear any non-processed jobs from thread queue

    return {
        'status': 'success',
        'detail': 'Deregister complete and server shutting down.',
    }


@app.get("/status")
async def check_status():
    """
    Checks the current prediction status of the model. Predictions are not able to be made
    until this method returns {"result": "True"}.

    :return: {"result": "True"} if model is ready for predictions, else {"result": "False"}
    """

    if not model_settings.ready_to_predict:
        raise PredictionException()

    return {
        'status': 'success',
        'detail': 'Model ready to receive prediction requests.'
    }


@app.post("/predict")
def receive_prediction(image_md5_hash: str = '', image_file_name: str = ''):
    """
    Creates a new prediction using the model. This method must be called after the init() method has run
    at least once, otherwise this will fail with a HTTP Error.

    :param image_md5_hash: ID of job from server
    :param image_file_name Image file name to predict on
    :return: Success message with job enqueued
    """

    # Ensure model is ready to receive prediction requests
    if not model_settings.ready_to_predict:
        raise PredictionException()

    dependency.prediction_queue.enqueue(
        predict_image, image_md5_hash, image_file_name, os.getenv('SERVER_PORT'), os.getenv('NAME'), job_id=image_md5_hash
    )

    return {
        'status': 'success',
        "detail": 'Prediction job pending. Result will be returned when complete.'
    }


def predict_image(image_hash, image_file_name, server_port, model_name):

    result = predict(image_file_name)  # Create prediction on model

    try:  # Send prediction results back to server
        headers = {
            'api_key': API_KEY
        }
        r = requests.post(
            'http://host.docker.internal:' + server_port + '/model/predict_result',
            headers=headers,
            json={
                'model_name': model_name,
                'image_hash': image_hash,
                'results': result
            }
        )
        r.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError):
        print('Unable to send prediction results to server. Hash: "' + image_hash + '"')
