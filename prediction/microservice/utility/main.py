import os
import requests
from model.model import predict, init
from model.info import model_name, model_tags


API_KEY = os.getenv('API_KEY')
SERVER_SOCKET = os.getenv('SERVER_SOCKET')

def register_to_server():
    """
    Registers a prediction model to the server. This will automatically register the correct name
    for the model.
    """
    try:  # Register to server
        headers = {'api_key': API_KEY}
        r = requests.post(
            SERVER_SOCKET + '/model/register',
            headers=headers,
            json={'name': model_name}
        )
        r.raise_for_status()
        if r.status_code != 200:
            return '[Error] Model Startup + Registration Unable to Authenticate. Model: [' + model_name +']'
        else:
            return 'Model Startup + Registration Successful. Model: [' + model_name +']'

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError):
        return '[Error] Model Startup + Registration Failure. Model: [' + model_name +']'



def predict_image(image_hash, image_file_name):

    # try:
    requests.get('http://host.docker.internal:5000')
    result = predict(image_file_name)  # Create prediction on model
    # except (e):
        # Do not send prediction results to server on crash. 
        # return '[Error] Model Prediction Crash. Model: [' + model_name +'] Hash:[' + image_hash + ']' 

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