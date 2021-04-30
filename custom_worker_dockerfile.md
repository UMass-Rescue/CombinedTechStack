# Custom Dockerfile for Prediction Worker

For any models that need specific libraries features that cannot be installed through pip or require a custom Dockerfile:

## Step 1

In ```combinedtechstack/.env``` file add variable 
```
PREDICTION_YOUR_MODEL=Your_model_folder_name
```
where ```Your_model_folder_name``` is the folder name in ```combinedtechstack/prediction/models``` containing the model.

## Step 2
Within the ```combinedtechstack/prediction/models/your_model_here``` add your custom ```Dockerfile```.

## Step 3
Navigate to the ```COMBINEDTECHSTACK/docker-compose.yml``` file and within it find the ```Prediction Microservice Workers``` section. 

## Step 4 
Create a new worker:
```
your_model_worker:
    container_name: ${PREDICTION_YOUR_MODEL}_worker
    command: python3 worker.py
    build:
      context: .
      dockerfile: prediction/models/${PREDICTION_YOUR_MODEL}/Dockerfile
      args:
        - MODEL_NAME=${PREDICTION_YOUR_MODEL}
    volumes:
      - ./prediction/models/${PREDICTION_YOUR_MODEL}:/app/model
      - prediction_images:/app/images
    environment:
      - GUNICORN_CMD_ARGS=--reload
      - API_KEY=${API_KEY_PREDICTION}
      - SERVER_SOCKET=${SERVER_SOCKET}
    depends_on:
      - redis
      - server
```

Where ```PREDICTION_YOUR_MODEL``` will be switched with your model paramater given in Step 1. Notably ```dockerfile: prediction/models/${PREDICTION_YOUR_MODEL}/Dockerfile ``` will point to your custom Dockerfile.
The worker will now be built using the custom Dockerfile.
