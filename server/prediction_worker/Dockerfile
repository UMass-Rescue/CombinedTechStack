FROM python:3.8

WORKDIR /app

# Load the model name from the docker-compose file
ARG MODEL_NAME 

# Copy the specific requirements file to our container for installing.
COPY "../../prediction/models/${MODEL_NAME}/requirements.txt" /app

# Install requirementss
RUN pip --no-cache-dir install -r requirements.txt

COPY server/prediction_worker/worker.py /app
COPY server/prediction_worker/utility/* /app/utility/