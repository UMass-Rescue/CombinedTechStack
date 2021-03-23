import base64
import logging
import os

import requests
from secrets import API_KEY
from src.model.model import predict, init
from src.server import dependency
from src.server.dependency import model_settings, pool, redis


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
