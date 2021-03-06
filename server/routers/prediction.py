import hashlib
import os
import shutil
from fastapi.responses import JSONResponse
from rq.registry import StartedJobRegistry

import dependency
from fastapi import File, UploadFile, HTTPException, Depends, APIRouter, Form
from rq.job import Job
from rq import Worker

from routers.auth import current_user_investigator
from dependency import redis, User, UniversalMLPredictionObject
from db_connection import add_object_db, add_user_to_object, get_objects_from_user_db, get_object_by_md5_hash_db, \
    add_filename_to_object, get_models_db, update_tags_to_object, update_role_to_tag_object
from typing import List
from rq import Queue
import uuid

model_router = APIRouter()


@model_router.get("/list", dependencies=[Depends(current_user_investigator)])
async def get_prediction_models(model_type: str = ''):
    """
    Returns a list of available models to the client. This will be filtered by an optional type of "image", "text",
    or "video". If no type is specified, then all available models will be returned
    """

    if model_type == '':
        get_available_prediction_models()

    return {"models": get_models_by_type(model_type)}


@model_router.get("/list/all", dependencies=[Depends(current_user_investigator)])
async def get_all_prediction_models():
    """
    Returns a list of every model that has ever been seen by the server, as well as the fields available in that model
    """
    all_models = get_models_db()
    return {'models': all_models}


@model_router.get("/tags", dependencies=[Depends(current_user_investigator)])
async def get_prediction_model_tags():
    """
    Returns list of tags for each available model
    """

    worker_data = [w.name.split(';') for w in Worker.all(redis)]
    valid_workers = {w[2]: w[3] for w in worker_data if w[0] == 'prediction'}

    return {"tags": valid_workers}


@model_router.get("/types", dependencies=[Depends(current_user_investigator)])
async def get_prediction_model_types():
    """
    Returns list of types for each available model
    """
    worker_data = [w.name.split(';') for w in Worker.all(redis)]
    valid_workers = {w[2]: w[1] for w in worker_data if w[0] == 'prediction'}

    return {"tags": valid_workers}


@model_router.post("/predict")
def create_new_prediction(models: List[str] = (),
                          model_type: str = Form(...),
                          objects: List[UploadFile] = File(...),
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
        # Ensure that the desired model is running
        if model not in get_available_prediction_models():
            invalid_models.append(model)

        # Ensure desired model is the correct type for input
        if model not in get_models_by_type(model_type):
            invalid_models.append(model)

    if invalid_models:
        error_message = "Invalid Models Specified: " + ''.join(list(set(invalid_models)))
        return HTTPException(status_code=400, detail=error_message)


    # Now we must hash each uploaded object to get a unique identifier
    # After hashing, we will store the object file temporarily in a Docker volume
    buffer_size = 65536  # Read object data in 64KB Chunks for hashlib
    processed_image_hashes = {}

    # Process uploaded objects
    for upload_file in objects:
        file_obj = upload_file.file
        md5 = hashlib.md5()

        # Obtain MD5 hash for uploaded object by reading it in blocks and updating the hash
        while True:
            data = file_obj.read(buffer_size)
            if not data:
                break
            md5.update(data)

        # Obtain final hash value and set the result dict
        hash_md5 = md5.hexdigest()
        processed_image_hashes[upload_file.filename] = hash_md5

        # Reset the file to the initial position for further processing
        file_obj.seek(0)

        # Either add object to database if it doesn't exist or get the current object from the database
        if get_object_by_md5_hash_db(hash_md5):
            prediction_obj = get_object_by_md5_hash_db(hash_md5)
        else:
            # Create a UniversalMLPredictionObject object to store data (dependency.py)
            prediction_obj = UniversalMLPredictionObject(**{
                'file_names': [upload_file.filename],
                'hash_md5': hash_md5,
                'type': model_type,
                'users': [current_user.username],
                'models': {},
                'user_role_able_to_tag': ['admin']
            })

            # If the type of the object is 'text' we add the text content to the object
            if model_type == 'text':
                prediction_obj.text_content = file_obj.read()

            # Add created object to database
            add_object_db(prediction_obj)

        # Associate the current user with the object that was uploaded
        add_user_to_object(prediction_obj, current_user.username)

        # Associate the name the file was uploaded under to the object
        add_filename_to_object(prediction_obj, upload_file.filename)

        # Copy object to the temporary storage volume for prediction
        if model_type != 'text':
            new_filename = hash_md5 + os.path.splitext(upload_file.filename)[1]
            stored_object_path = "/app/prediction/" + new_filename
            stored_object = open(stored_object_path, 'wb+')
            shutil.copyfileobj(file_obj, stored_object)

            for model in models:
                Queue(name=model, connection=redis).enqueue(
                    'utility.main.predict_object', hash_md5, new_filename, job_id=hash_md5 + model + str(uuid.uuid4())
                )
        # just for text, because instead of file_name, text predict takes the text content
        else:
            text_content = file_obj.read()
            text_content = text_content.decode('UTF-8')
            for model in models:
                Queue(name=model, connection=redis).enqueue(
                    'utility.main.predict_object', hash_md5, text_content, job_id=hash_md5 + model + str(uuid.uuid4())
                )

    return {"prediction objects": [processed_image_hashes[key] for key in processed_image_hashes]}


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
    for model in get_available_prediction_models():
        all_jobs.update(
            StartedJobRegistry(model, connection=redis).get_job_ids() + Queue(model, connection=redis).job_ids)

    for md5_hash in md5_hashes:

        object = get_object_by_md5_hash_db(md5_hash)  # Get object
        found_pending_job = False
        for job_id in all_jobs:
            if md5_hash in job_id and Job.fetch(job_id, connection=redis).get_status() != 'finished':
                found_pending_job = True
                results.append({
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
            return JSONResponse(
                status_code=404,
                content={
                    'detail': 'Unable to find result for specified hash',
                    'hash': md5_hash
                }
            )

        # If everything is successful with object, return data
        results.append({**object.dict()})
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
    num_objects = db_result['num_objects']
    page_size = dependency.PAGINATION_PAGE_SIZE

    if page_id <= 0:
        return {
            'num_pages': num_pages,
            'page_size': page_size,
            'num_objects': num_objects
        }
    elif page_id > num_pages:
        return JSONResponse(
            status_code=400,
            content={
                'detail': 'Page does not exist.',
                'num_pages': num_pages,
                'page_size': page_size,
                'num_objects': num_objects,
                'current_page': page_id
            }
        )

    return {
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
        return JSONResponse(
            status_code=400,
            content={
                'detail': 'You must specify a search string or search filter'
            }
        )

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
        'hashes': hashes
    }


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
async def update_object_tag_roles(md5_hashes: List[str], username: str, remove_roles: List[str] = [],
                                  new_roles: List[str] = []):
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


def get_available_prediction_models():
    """
    Generates a list of all models connected to the server.
    """
    worker_data = [w.name.split(';') for w in Worker.all(redis)]
    valid_workers = set(w[2] for w in worker_data if w[0] == 'prediction')
    return list(valid_workers)

  
@model_router.post("/tag/update")
async def update_image_tags(md5_hashes: List[str], username: str, new_tags: List[str] = []):
    """
    Find list of images and add tags into its universalMLimage object "tags" field

    :param md5_hashes: List of hashes for universal ml image object
    :param username: username of the current user
    :param new_tags: list of image tags that need to be added to image object
    :return: json with status and detail
    """
    result = update_tags_to_image(md5_hashes, username, new_tags)
    return result



def get_models_by_type(model_type):
    """
    Returns list of types for each available model
    """
    worker_data = [w.name.split(';') for w in Worker.all(redis)]
    valid_workers = {w[2]: w[1] for w in worker_data if w[0] == 'prediction'}

    retModels = []
    for key, value in valid_workers.items():
        if model_type in value:
            retModels.append(key)

    return list(set(retModels))
