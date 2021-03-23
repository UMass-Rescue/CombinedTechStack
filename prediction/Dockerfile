FROM python:3.7

WORKDIR /app

COPY microservice/main.py /app
COPY microservice/worker.py /app

# Load the model name from the docker-compose file
ARG MODEL_NAME 

# Copy the specific requirements file to our container for installing.
COPY "./models/${MODEL_NAME}/requirements.txt" /app

# Install requirements.
RUN pip --no-cache-dir install -r requirements.txt