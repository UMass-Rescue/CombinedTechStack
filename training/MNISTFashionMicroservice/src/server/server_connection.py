import os

import requests
import time

from fastapi.logger import logger

from src.server import dependency

API_KEY = os.getenv('API_KEY')

def register_model_to_server(server_port, dataset_port, dataset_name):
    """
    Send notification to the server with the training name and port to register the microservice
    It retries until a connection with the server is established
    """
    while not dependency.shutdown:
        try:
            headers = {
                'api_key': API_KEY
            }
            r = requests.post('http://host.docker.internal:' + str(server_port) + '/training/register',
                              headers=headers,
                              json={"name": dataset_name, "socket": 'http://host.docker.internal:'+dataset_port})
            r.raise_for_status()
            dependency.connected = True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError):
            dependency.connected = False
            logger.debug('Registering to server fails. Retry in ' + str(dependency.WAIT_TIME) + ' seconds')

        # Delay for WAIT_TIME between server registration pings
        for increment in range(dependency.WAIT_TIME):
            if not dependency.shutdown:  # Check between increments to stop hanging on shutdown
                time.sleep(1)

    logger.debug("[Healthcheck] Server Registration Thread Halted.")