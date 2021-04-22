import hashlib
import os
import shutil
import time

from rq.registry import StartedJobRegistry
from starlette import status
from starlette.responses import JSONResponse

import dependency
import requests
from fastapi import File, UploadFile, HTTPException, Depends, APIRouter
from rq.job import Job

from routers.auth import current_user_investigator
from dependency import logger, MicroserviceConnection, settings, redis, User, pool, UniversalMLPredictionObject, object_collections
from db_connection import add_object_db, add_user_to_object, get_objects_from_user_db, get_object_by_md5_hash_db, \
    get_api_key_by_key_db, add_filename_to_object, add_model_to_object_db, get_models_db, add_model_db, \
    update_tags_to_object, update_role_to_tag_object
from typing import List
from rq import Queue
import uuid


model_router = APIRouter()


@model_router.get("/list", dependencies=[Depends(current_user_investigator)])
async def get_available_prediction_models():
    """
    Returns list of available models to the client. This list can be used when calling get_prediction,
    with the request
    """
    return {"models": [*settings.available_models]}


@model_router.get("/all", dependencies=[Depends(current_user_investigator)])
async def get_all_prediction_models():
    """
    Returns a list of every model that has ever been seen by the server, as well as the fields available in that model
    """
    all_models = get_models_db()
    return {'models': all_models}


@model_router.post("/predict")
def create_new_prediction(objects: List[UploadFile] = File(...),
                                   models: List[str] = (),
                                   current_user: User = Depends(current_user_investigator)):
    """
    Create a new prediction request for any number of objects on any number of models. This will enqueue the jobs
    and a worker will process them and get the results. Once this is complete, a user may later query the job
    status by the unique key that is returned from this method for each object uploaded.

    :param current_user: User object who is logged in
    :param objects: List of file objects that will be used by the models for prediction
    :param models: List of models to run on objects
    :return: Unique keys for each object uploaded in objects.
    """

    # Start with error checking on the models list.
    # Ensure that all desired models are valid.
    if not models:
        return HTTPException(status_code=400, detail="You must specify models to process objects with")

    invalid_models = []
    for model in models:
        if model not in settings.available_models:
            invalid_models.append(model)

    if invalid_models:
        error_message = "Invalid Models Specified: " + ''.join(invalid_models)
        return HTTPException(status_code=400, detail=error_message)

    # Now we must hash each uploaded object
    # After hashing, we will store the object file on the server.

    buffer_size = 65536  # Read object data in 64KB Chunks for hashlib
    hashes_md5 = {}

    # Process uploaded objects
    for upload_file in objects:
        file = upload_file.file
        type = "video" #TODO: FIND THIS FIELD FROM UPLOAD FILE
        print(type)
        md5 = hashlib.md5()
        while True:
            data = file.read(buffer_size)
            if not data:
                break
            md5.update(data)

        # Process object
        hash_md5 = md5.hexdigest()
        hashes_md5[upload_file.filename] = hash_md5

        file.seek(0)

        if get_object_by_md5_hash_db(hash_md5, type):
            object = get_object_by_md5_hash_db(hash_md5, type)
        else:  # If object does not already exist in db

            # Create a UniversalMLPredictionObject object to store data
            object = UniversalMLPredictionObject(**{
                'file_names': [upload_file.filename],
                'hash_md5': hash_md5,
                'type': type, 
                'hash_sha1': 'TODO: Remove This Field',
                'hash_perceptual': 'TODO: Remove This Field',
                'users': [current_user.username],
                'models': {},
                'user_role_able_to_tag': ['admin']
            })

            # Add created object to database
            add_object_db(object)

        # Associate the current user with the object that was uploaded
        add_user_to_object(object, current_user.username)

        # Associate the name the file was uploaded under to the object
        add_filename_to_object(object, upload_file.filename)

        # Copy object to the temporary storage volume for prediction
        new_filename = hash_md5 + os.path.splitext(upload_file.filename)[1]
        stored_object_path = "/app/prediction/" + new_filename
        stored_object = open(stored_object_path, 'wb+')
        shutil.copyfileobj(file, stored_object)

        for model in models:
            dependency.prediction_queues[model].enqueue(
                'utility.main.send_prediction', hash_md5, new_filename, type, job_id=hash_md5+model+str(uuid.uuid4())
            )


    return {"prediction objects": [hashes_md5[key] for key in hashes_md5]}

@model_router.post("/results", dependencies=[Depends(current_user_investigator)])
async def get_jobs(md5_hashes: List[str]):
    """
    Returns the prediction status for a list of jobs, specified by md5 hash.

    :param md5_hashes: List of object md5 hashes
    :return: Array of prediction results.
    """
    results = []

    if not md5_hashes:
        return []

    # If there are any pending predictions, alert user and return existing ones
    # Since job_id is a composite hash+model, we must loop and find all jobs that have the
    # hash we want to find. We must get all running and pending jobs to return the correct value
    all_jobs = set()
    for model in settings.available_models:
        all_jobs.update(StartedJobRegistry(model, connection=redis).get_job_ids() + dependency.prediction_queues[model].job_ids)

    for md5_hash in md5_hashes:

        #TO DO: change this function to not take type
        object = get_object_by_md5_hash_db(md5_hash, "video")  # Get object
        found_pending_job = False
        for job_id in all_jobs:
            if md5_hash in job_id and Job.fetch(job_id, connection=redis).get_status() != 'finished':
                found_pending_job = True
                results.append({
                    'status': 'success',
                    'detail': 'Object has pending predictions. Check back later for all model results.',
                    **object.dict()
                })
                break  # Don't look for more jobs since we have found one that is pending

        # If we have found a job that is pending, then move on to next object
        if found_pending_job:
            continue

        # If we haven't found a pending job for this object, and it doesn't exist in our database, then that
        # means that the object hash must be invalid.
        if not object:
            results.append({
                'status': 'failure',
                'detail': 'Unknown md5 hash specified.',
                'hash_md5': md5_hash
            })
            continue

        # If everything is successful with object, return data
        results.append({
            'status': 'success',
            **object.dict()
        })
    return results


@model_router.post("/search")
def search_objects(
        current_user: User = Depends(current_user_investigator),
        page_id: int = -1,
        search_string: str = '',
        search_filter: dependency.SearchFilter = None,
):
    """
    Returns a list of object hashes of objects submitted by a user. Pagination of object hashes as
    well as searching is provided by this method.

    :param current_user: User currently logged in
    :param page_id: Optional int for individual page of results (From 1...N)
    :param search_filter Optional filter to narrow results by models
    :param search_string Optional string to narrow results by metadata field
    :return: List of hashes user has submitted (by page) and number of total pages. If no page is provided,
             then only the number of pages available is returned.
    """

    # Parse the search filter from the request body
    if not search_filter:
        search_filter = {}
    else:
        search_filter = search_filter.search_filter

    db_result = get_objects_from_user_db(current_user.username, page_id, search_filter, search_string)
    num_pages = db_result['num_pages']
    hashes = db_result['hashes'] if 'hashes' in db_result else []
    num_objects = db_result['objects']
    page_size = dependency.PAGINATION_PAGE_SIZE

    if page_id <= 0:
        return {
            'status': 'success',
            'num_pages': num_pages,
            'page_size': page_size,
            'num_objects': num_objects
        }
    elif page_id > num_pages:
        return {
            'status': 'failure',
            'detail': 'Page does not exist.',
            'num_pages': num_pages,
            'page_size': page_size,
            'num_objects': num_objects,
            'current_page': page_id}

    return {
        'status': 'success',
        'num_pages': num_pages,
        'page_size': page_size,
        'num_objects': num_objects,
        'current_page': page_id,
        'hashes': hashes
    }


@model_router.post('/search/download')
def download_search_object_hashes(
        current_user: User = Depends(current_user_investigator),
        search_string: str = '',
        search_filter: dependency.SearchFilter = None
):
    """
    Returns a list of all object hashes that match a search criteria. This is used for downloading on the client-side
    bulk object information.

    :param current_user: Currently logged in user
    :param search_string: String to search metadata field of UniversalMLPredictionObject object
    :param search_filter: Model JSON search for matching fields
    :return: List of object hashes associated with user
    """
    if search_string == '' and not search_filter:
        return {
            'status': 'failure',
            'detail': 'You must specify a search string or search filter'
        }

    if not search_filter:
        filter_to_use = {}
    else:
        filter_to_use = search_filter.search_filter

    db_result = get_objects_from_user_db(
        current_user.username,
        search_filter=filter_to_use,
        search_string=search_string,
        paginate=False
    )
    hashes = db_result['hashes']

    return {
        'status': 'success',
        'hashes': hashes
    }


def get_api_key(api_key_header: str = Depends(dependency.api_key_header_auth)):
    """
    Validates an API key contained in the header. This also ensures that the API key is authorized to
    make prediction requests.

    :param api_key_header: Request header containing {'API_KEY': 'someKeyValue'}
    :return: APIKeyData object on success, else will raise HTTP CredentialException
    """

    api_key_data = get_api_key_by_key_db(api_key_header)
    if not api_key_data or not api_key_data.enabled or api_key_data.type != dependency.ExternalServices.predict_microservice.name:
        raise dependency.CredentialException
    return api_key_data


@model_router.post("/register", dependencies=[Depends(get_api_key)])
def register_model(model: MicroserviceConnection):
    """
    Register a single model to the server by adding the model's name and socket
    to available model settings. Also kick start a separate thread to keep track
    of the model service status. Models that are registered must use a valid API key.

    :param model: MicroserviceConnection object with the model name and model socket.
    :return: {'status': 'success'} if registration successful else {'status': 'failure'}
    """


    # Do not add duplicates of running models to server
    if model.name in settings.available_models:
        return {
            "status": "success",
            'model': model.name,
            'detail': 'Model has already been registered.'
        }


    # Register model as available and add its queue
    settings.available_models.add(model.name)
    dependency.prediction_queues[model.name] = Queue(model.name, connection=redis)

    logger.debug("Model " + model.name + " successfully registered to server.")

    return {
        "status": "success",
        'model': model.name,
        'detail': 'Model has been successfully registered to server.'
    }

@model_router.post('/predict_result', dependencies=[Depends(get_api_key)])
def receive_prediction_results(model_prediction_result: dependency.ModelPredictionResult):
    """
    Helper method that a worker will use to generate a prediction for a given model. This will be run in a task
    by any redis queue worker that is registered.

    :param model_prediction_result Prediction results from server
    """

    # Receive Prediction from Model
    model_result = model_prediction_result.results['result']
    model_classes = model_prediction_result.results['classes']

    if object_collections[model_prediction_result.type].find_one({"hash_md5": model_prediction_result.hash}):
        object = get_object_by_md5_hash_db(model_prediction_result.hash, model_prediction_result.type)
    add_model_to_object_db(object, model_prediction_result.model_name, model_result)
    add_model_db(model_prediction_result.model_name, model_classes, model_prediction_result.type)


@model_router.post("/tag/update")
async def update_tags(md5_hashes: List[str], username: str, remove_tags: List[str] = [], new_tags: List[str] = []):
    """
    Find list of objects and add tags into its universalMLPredictionPbject "tags" field

    :param md5_hashes: List of hashes for universal ml object
    :param username: username of the current user
    :param remove_tags: list of tags that needs to remove
    :param new_tags: list of tags that need to be added to the object
    :return: json with status and detail
    """
    result = update_tags_to_object(md5_hashes, username, remove_tags, new_tags)
    return result


@model_router.post("/tag/role/update")
async def update_object_tag_roles(md5_hashes: List[str], username: str, remove_roles: List[str] = [], new_roles: List[str] = []):
    """
    Find an object and add roles_able_to_tag into its universalMLpredictionobject object "user_role_able_to_tag" field, so that role can update 
    that object's tags

    :param md5_hashes: List of hashes for universal ml object 
    :param username: username of the current user
    :param remove_roles: remove list of roles that are authenticated to edit object tags
    :param new_roles: adding list of roles that are allowed to edit object tags
    :return: json with status and detail
    """
    result = update_role_to_tag_object(md5_hashes, username, remove_roles, new_roles)
    return result

