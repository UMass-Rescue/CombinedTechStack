import time
import os

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

    current_time = time.time()

    for f in os.listdir('./prediction_images/'):
        creation_time = os.path.getctime(f)
        if (current_time - creation_time) // (24 * 3600) >= 1:  # Check if file is older than 1 day
            os.remove(f) # Delete files older than 1 day

    for _ in range(60*60):  # Delay for an hour
        time.sleep(1)



@app.on_event('startup')
def on_startup():
    """
    On server startup, schedule 
    """
    pool.submit()



@app.on_event('shutdown')
def on_shutdown():
    """
    On server shutdown, stop all background model pinging threads.
    """

    pool.shutdown()  # Clear any non-processed jobs from thread queue

