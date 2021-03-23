import os
import requests
from model.model import predict, init

API_KEY = os.getenv('API_KEY')
SERVER_SOCKET = os.getenv('SERVER_SOCKET')


def predict_image(image_hash, image_file_name):

    try:
        result = predict(image_file_name)  # Create prediction on model
    except (e):
        print('[Error] Model Prediction Crash. Model: [' + model_name +'] Hash:[' + image_hash + ']')
        return  # Do not send prediction results to server on crash. 

    try:  # Send prediction results back to server
        headers = {
            'api_key': API_KEY
        }
        r = requests.post(
            SERVER_SOCKET + '/model/predict_result',
            headers=headers,
            json={
                'model_name': model_name,
                'image_hash': image_hash,
                'results': result
            }
        )
        r.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError):
        print('[Error] Model Result Sending Failure. Model: [' + model_name +'] Hash:[' + image_hash + ']')