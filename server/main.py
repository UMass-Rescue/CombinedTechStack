import time
import os
import pathlib
import datetime

from fastapi.logger import logger

import dependency
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from starlette.responses import JSONResponse

from dependency import CredentialException, pool
from routers.auth import auth_router
from routers.prediction import model_router
from routers.training import training_router


# App instance used by the server 
app = FastAPI()

# --------------------------------------------------------------------------
#                        | Router Registration |
#                        |---------------------|
# In order for groups of routes to work with the server, they must be added
# below here with a specific router. Routers act as an "app instance" that
# can be used from outside of the main.py file. The specific code for each
# router can be found in the routers/ folder.
#
# --------------------------------------------------------------------------

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"],
    responses={404: {"detail": "Not found"}},
)

app.include_router(
    model_router,
    prefix="/model",
    tags=["models"],
    responses={404: {"detail": "Not found"}},
)

app.include_router(
    training_router,
    prefix="/training",
    tags=["training"],
    responses={404: {"detail": "Not found"}},
)


@app.exception_handler(CredentialException)
async def credential_exception_handler(request: Request, exc: CredentialException):
    """
    Handler for credential exception. This type of exception is raised when a client attempts to access an endpoint
    without sufficient permissions for endpoints that are protected by OAuth2. This exception is raised if the client
    has no bearer token, if the bearer token is expired, or if their account does not have sufficient permissions/roles
    to access a certain endpoint.

    :param request: HTTP Request object
    :param exc: Exception
    :return: 401 HTTP Exception with authentication failure message
    """
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "status": 'failure',
            "detail": "Unable to validate credentials."
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


# -------------------------------
# Web Server Configuration
# -------------------------------

# Cross Origin Request Scripting (CORS) is handled here.
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5057",
    "http://localhost:5000",
    "http://localhost:6005",
    "http://localhost:6379",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------
# Basic Routes
# -------------------------------


@app.get("/")
async def root():
    """
    Root endpoint that validates the server is running. This requires no authentication to call, and will always
    return the same result so long as the server is running.
    :return: {'status': 'success'} if server is running, else no HTTP response.
    """
    return {
        "status": "success",
        "detail": 'PhotoAnalysisServer is Running'
    }


def delete_unused_files():
    """
    Scheduled thread that will check all uploaded images every hour and delete them if they
    have not been accessed recently.
    """

    current_time = datetime.timedelta(hours=-4) + datetime.datetime.now()

    for file_name in os.listdir('./prediction_images/'):

        file_creation_time = datetime.datetime.fromtimestamp(
            pathlib.Path('./prediction_images/' + file_name).stat().st_ctime
        )

        time_since_file_creation = current_time - file_creation_time

        if time_since_file_creation.days >= 1:
            os.remove('./prediction_images/' + file_name)
            logger.debug('[Automated Deletion Thread] Removed Image File [' + file_name + ']')


    # Delay for an hour between deletion checks
    for _ in range(60*60):  
        if not dependency.shutdown:  # Check between increments to stop hanging on shutdown
            time.sleep(1) 
        else:
            break

    if dependency.shutdown:
        logger.debug('Image Deletion Thread Terminated')



@app.on_event('startup')
def on_startup():
    """
    On server startup, schedule
    """ 

    pool.submit(delete_unused_files) 



@app.on_event('shutdown') 
def on_shutdown():
    """
    On server shutdown, stop all background model pinging threads.
    """
    dependency.shutdown = True
    pool.shutdown(wait=True)
