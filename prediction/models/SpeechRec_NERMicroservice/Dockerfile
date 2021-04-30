FROM python:3.8

WORKDIR /app

# COPY ../../server/prediction_worker/worker.py /app
# COPY ../../server/prediction_worker/utility/* /app/utility/

COPY server/prediction_worker/worker.py /app
COPY server/prediction_worker/utility/* /app/utility/


# Load the model name from the docker-compose file
ARG MODEL_NAME 

# Copy the specific requirements file to our container for installing.
COPY ./prediction/models/${MODEL_NAME}/requirements.txt /app

# Install requirements.
RUN pip --no-cache-dir install -r requirements.txt

RUN apt-get update && \
      apt-get -y install sudo
RUN sudo apt-get install libsndfile1 -y