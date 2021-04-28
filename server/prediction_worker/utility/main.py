import os
import requests
from model.model import predict, init
from model.config import model_name, model_tags, model_type
from worker import shutdown
import time


API_KEY = os.getenv('API_KEY')
SERVER_SOCKET = os.getenv('SERVER_SOCKET')

def register_to_server():
    """
    Registers a prediction model to the server. This will automatically register the correct name
    for the model.
    """

    while not shutdown:
        try:  # Register to server
            headers = {'api_key': API_KEY}
            r = requests.post(
                SERVER_SOCKET + '/model/register',
                headers=headers,
                json={'name': model_name,
                      'type': model_type}
            )
            r.raise_for_status()
            if r.status_code != 200:
                print('[Error] Model Registration Unable to Authenticate to Server. Model: [' + model_name +']')

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError):
            print('[Error] Model Registration Unable to Connect to Server. Model: [' + model_name +']')

        # After sending request, we will wait before re-registering to server.
        sleepTimeInSeconds = 10
        while sleepTimeInSeconds > 0 and not shutdown:
            time.sleep(1)
            sleepTimeInSeconds -= 1

    print('[Worker] Registration Thread Shutting down.')


def send_prediction(hash, file_name, type):
    # try:

    result = predict(file_name)  # Create prediction on model
    
    # except:
    #     # Do not send prediction results to server on crash. 
    #     print('[Error] Model Prediction Crash. Model: [' + model_name + '] Hash:[' + image_hash + ']')
    #     return

    try:  # Send prediction results back to server
        headers = {
            'api_key': API_KEY
        }
        r = requests.post(
            SERVER_SOCKET + '/model/store_prediction',
            headers=headers,
            json={
                'model_name': model_name,
                'hash': hash,
                'results': result,
                'file_type': type
            }
        )
        r.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError):
        print('[Error] Model Result Sending Failure. Model: [' + model_name +'] Hash:[' + hash + ']')