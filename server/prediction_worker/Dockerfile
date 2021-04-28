FROM python:3.8

WORKDIR /app

COPY server/prediction_worker/worker.py /app
COPY server/prediction_worker/utility/* /app/utility/


# Load the model name from the docker-compose file
ARG MODEL_NAME 

# Copy the specific requirements file to our container for installing.
COPY "../../prediction/models/${MODEL_NAME}/requirements.txt" /app

# Include this line if using opencv for a video model.
RUN apt-get -y update && apt-get install -y python3-opencv

# Install requirementss
RUN pip --no-cache-dir install -r requirements.txt