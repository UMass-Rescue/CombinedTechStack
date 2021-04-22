from typing import Union, List

from dependency import User, user_collection, PAGINATION_PAGE_SIZE, UniversalMLPredictionObject, Roles, \
    APIKeyData, object_collections,\
    api_key_collection, model_collection, TrainingResult, training_collection, logger
import math
import json


# ---------------------------
# User Database Interactions
# ---------------------------


def add_user_db(user: User) -> bool:
    """
    Adds a new user to the database.

    :param user: User object to add to database
    :return: True if added, else False if error.
    """

    # If request didn't specify permissions, ensure that none are stored in the database.
    if user.roles is None:
        roles = []

    if not user_collection.find_one({"username": user.username}):
        user_collection.insert_one(user.dict())
        return True

    return False  # This means there is already a user in the database with this name.


def get_user_by_name_db(username: str) -> Union[User, None]:
    """
    Finds a user in the database by a given username.

    :param username: username of user
    :return: User object if user with given username exists, else None
    """
    if not user_collection.find_one({"username": username}):
        return None

    database_result = user_collection.find_one({"username": username})
    user_object = User(**database_result)
    return user_object


def set_user_roles_db(username: str, updated_roles: list) -> bool:
    """
    Sets the roles for a given user.

    :param username: Username of user that will have roles modified
    :param updated_roles: Array of roles that user will now have
    :return: Success: True or False
    """
    if not user_collection.find_one({"username": username}):
        return False

    user_collection.update_one({'username': username}, {'$set': {'roles': updated_roles}})
    return True


# ---------------------------
# API Key Database Interactions
# ---------------------------

def add_api_key_db(key: APIKeyData) -> dict:
    """
    Adds a new API key into the database.

    :param key: APIKeyData object to be added to database
    :return: {'status': 'success'} if added, else {'status': 'failure'}
    """

    if not api_key_collection.find_one({"key": key.key}):
        api_key_collection.insert_one(key.dict())
        return {'status': 'success', 'detail': 'API key successfully added.'}
    else:
        return {'status': 'failure', 'detail': 'API key with desired key already exists.'}


def get_api_key_by_key_db(key: str) -> Union[APIKeyData, None]:
    """
    Gets an API key object from the key string.

    :param key: API key string to lookup
    :return: APIKeyData if key with given ID exists, else NoneType if no API key for a given key string exists.
    """
    if not api_key_collection.find_one({"key": key}):
        return None

    database_result = api_key_collection.find_one({"key": key})
    api_key_object = APIKeyData(**database_result)
    return api_key_object


def get_api_keys_by_user_db(user: User) -> List[APIKeyData]:
    """
    Finds all API keys which are activate and associated with a given user account.

    :param user: User object to find API keys associated with it
    :return: List of APIKeyData for all keys associated with user. Returns [] if no keys found.
    """
    if not api_key_collection.find_one({"user": user.username}):
        return []

    database_results = list(api_key_collection.find({"user": user.username, 'enabled': True}))
    user_keys = [APIKeyData(**res) for res in database_results]
    return user_keys


def set_api_key_enabled_db(key: APIKeyData, enabled: bool) -> bool:
    """
    Enables or disables a given API key.

    :param key: APIKeyData object that is being modified in the DB
    :param enabled: Key will be enabled (True) or disabled (False)
    :return: Success: True or False
    """
    if not api_key_collection.find_one({"key": key.key}):
        return False

    api_key_collection.update_one({'key': key.key}, {'$set': {'enabled': enabled}})
    return True


# ---------------------------
# Prediction Object Database Interactions
# ---------------------------

def add_object_db(object: UniversalMLPredictionObject):
    """
    Adds a new object to the database based on the UniversalMLPredictionObject model.

    :param object: UniversalMLPredictionObject to add to database.
    """

    if not object_collections[object.type].find_one({"hash_md5": object.hash_md5}):
        object_collections[object.type].insert_one(object.dict())


def add_user_to_object(object: UniversalMLPredictionObject, username: str):
    """
    Adds a user account to a UniversalMLPredictionObject record. This is used to track which users upload objects.

    :param v: UniversalMLPredictionObject to update
    :param username: Username of user who is accessing object
    """
    if object_collections[object.type].find_one({"hash_md5": object.hash_md5}):
        existing_users = list(object_collections[object.type].find_one({"hash_md5": object.hash_md5})['users'])
        if username not in existing_users:  # Only update if not in list already
            existing_users.append(username)
            object_collections[object.type].update_one(
                {"hash_md5": object.hash_md5},
                {'$set': {'users': existing_users}}
            )


def add_filename_to_object(object: UniversalMLPredictionObject, filename: str):
    """
    Adds a filename to a UniversalMLPredictionObject record. This is used to track all file names that an object is uploaded to
    the server under. An object file is considered "the same" if their md5 hashes are identical.

    :param object: UniversalMLPredictionObject to update
    :param filename: file name with extension
    """
    if object_collections[object.type].find_one({"hash_md5": object.hash_md5}):
        current_names = list(object_collections[object.type].find_one({"hash_md5": object.hash_md5})['file_names'])
        if filename not in current_names:  # Only update if not in list already
            current_names.append(filename)
            object_collections[object.type].update_one(
                {"hash_md5": object.hash_md5},
                {'$set': {'file_names': current_names}}
            )


def add_model_to_object_db(object: UniversalMLPredictionObject, model_name, result):
    """
    Adds prediction data to a UniversalMLPredictionObject object. This is normally called when a prediction microservice
    returns data to the server with the results of a prediction request. The 'metadata' field is always updated.
    in this method as a string to enable easy querying of nested model results.

    :param object: UniversalMLPredictionObject to add prediction data to
    :param model_name: Name of model that was run on the object.
    :param result: JSON results of the training
    """

    new_metadata = [list(object.dict()['models'].values()), model_name, result] + object.file_names
    metadata_str = json.dumps(new_metadata)
    for char_to_replace in ['"', "'", "\\", '[', ']', '{', '}']:
        metadata_str = metadata_str.replace(char_to_replace, '')

    object_collections[object.type].update_one({'hash_md5': object.hash_md5}, {'$set': {
        'models.' + model_name: result,
        'metadata': metadata_str
    }})


def get_objects_from_user_db(
        username: str,
        page: int = -1,
        search_filter: dict = None,
        search_string: str = '',
        paginate: bool = True
):
    """
    Returns a list of object hashes associated with a username. This method also has pagination support and if a page
    number is provided, then it will return dependency.PAGINATION_PAGE_SIZE object hashes. If the username of the user
    in this request is an administrator, then all object in the server will be queried. Otherwise, only UniversalMLPredictionObject
    objects that contain the username will be included in the results.

    This method also has unique functionality to allow for filtering of object results. If these values are provided,
    the mongo query will be filtered based on the fields available in search_filter and search_string.

    :param username: Username of user to get objects for
    :param page: Page to return of results. Will return all objects if page is -1
    :param search_filter Optional filter to narrow down query
    :param search_string String that will be matched against object metadata
    :param paginate Return all results or only page
    :return: Dictionary of object hashes, total pages
    """

    user = get_user_by_name_db(username)
    if not user:  # If user does not exist, return empty
        return [], 0

    return_value = dict.fromkeys(object_collections.keys)
    # loop through collections and search.
    for type in object_collections.keys():
        # If there is a filter, start with the correct dataset that has been filtered already
        # Generate the result of the query in this step
        if search_filter or search_string:
            # List comprehension to take the inputted filter and make it into a pymongo query-compatible expression
            search_params = []
            if search_filter:  # Append search filter
                flat_model_filter = (
                    [{'models.' + model + '.' + str(model_class): {'$gt': 0}} for model in search_filter for model_class in
                    search_filter[model]])
                search_params.append({'$or': flat_model_filter})
            if search_string:  # Append search string
                search_params.append({"metadata": {'$regex': search_string, '$options': 'i'}})
            if Roles.admin.name not in user.roles:  # Add username to limit results if not admin
                search_params.append({'users': username})

            result = object_collections[type].find({'$and': search_params}, {"hash_md5"})
        else:
            if Roles.admin.name in user.roles:
                result = object_collections[type].find({}, {"hash_md5"})
            else:
                result = object_collections[type].find({'users': username}, {"hash_md5"})

        # If we are getting a specific page of objects, then generate the list of hashes
        final_hash_list = []
        if page > 0 and paginate:
            # We use this for actual db queries. Page 1 = index 0
            page_index = page - 1
            final_hash_list = result.skip(PAGINATION_PAGE_SIZE * page_index).limit(PAGINATION_PAGE_SIZE)

            # After query, convert the result to a list
            final_hash_list = [object_map['hash_md5'] for object_map in list(final_hash_list)]
        elif not paginate:  # Return all results
            final_hash_list = [object_map['hash_md5'] for object_map in list(result)]

        num_objects = result.count()
        object_value = {
            "hashes": final_hash_list,
            "num_objects": num_objects
        }
        if paginate:
            object_value["num_pages"] = math.ceil(num_objectss / PAGINATION_PAGE_SIZE)
        return_value[type] = object_value
        
    return return_value


def get_models_from_object_db(object: UniversalMLPredictionObject, model_name: str = ""):
    """
    Creates a dictionary of all models with prediction results for a given object. This is returned
    in the format of {modelName: result1, ...}.

    :param object: UniversalMLPredictionObject to obtain model results from
    :param model_name: Optional filter to return specific model name
    :return: Dictionary of model results
    """

    projection = {
        "_id": 0,
        "models": 1
    }

    if not object_collections[object.type].find_one({"hash_md5": object.hash_md5}):
        return {}

    if model_name != "":
        results = object_collections[object.type].find_one({"hash_md5": object.hash_md5}, projection)
        return {model_name: results['models'][model_name]}
    else:
        return object_collections[object.type].find_one({"hash_md5": object.hash_md5}, projection)['models']


# TO DO: make it so type doesn't have to be a parameter...
def get_object_by_md5_hash_db(object_hash, type) -> Union[UniversalMLPredictionObject, None]:
    """
    Locates an object data by its md5 hash, and then creates a UniversalMLPredictionObject object with that data.

    :param object_hash: md5 hash of object to search for
    :return: UniversalMLPredictionObject object of object with a md5 hash, or None if not found
    """
    if not object_collections[type].find_one({"hash_md5": object_hash}):
        return None

    result = object_collections[type].find_one({"hash_md5": object_hash})
    result.pop('_id')
        
    return UniversalMLPredictionObject(**result)



def update_tags_to_object(hashes_md5: [str], username: str, remove_tags: [str], new_tags: [str]):
    """
    This method recieves two tags, where user can choose an tag and update it into a new tag

    param:
        username: user that is updating the tags
    request body:
        hashes_md5: list of md5 hashes
        remove_tags: list of tags needs to be remove from objects, default []
        new_tags: list of tags needs to be added to objects, default []
    return:
        always return a list with status message in it
    """
    result = []
    user = get_user_by_name_db(username)
    if user:
        roles = user.roles
        for hash_md5 in hashes_md5:
            if get_object_by_md5_hash_db(hash_md5):
                object = get_object_by_md5_hash_db(hash_md5)
                authed_roles = object['user_role_able_to_tag']
                if set(roles) & set(authed_roles): # update tags here
                    existing_tags = object['tags']
                    existing_tags = list(set(existing_tags) - set(remove_tags) - set(new_tags))
                    existing_tags = existing_tags + new_tags
                    object.update_one(
                    {"hash_md5": hash_md5},
                    {'$set': {'tags': list(existing_tags)}}
                    )
                    result.append({'status': 'success', 'detail': hash_md5 + ' updated tags'})
                else:
                    result.append({'status': 'failure', 'detail': hash_md5 + ' not authorized'})
            else: # if object not found
                result.append({'status': 'failure', 'detail': hash_md5 + ' not found'})
        return result
    return [{'status': 'failure', 'detail': 'User does not exist'}]
   

# TODO: Current any roles can change the user_role_able_to_tag field under object object, change the following mark line to limit access
def update_role_to_tag_object(hashes_md5: [str], username: str, remove_roles: [str], new_roles: [str]):
    """
    Update new authorized tagging role to the object, so user with that role can
    add or remove tag for that object

    :param username: username of the current user
    :request body:
        hashes_md5: list of md5 hashes
        remove_roles: list of roles needs to be remove from objects, default []
        new_roles: list of roles needs to be added to objects, default []
    """
    result = []
    user = get_user_by_name_db(username)
    if user:
        if set(user.roles) & {"admin", "investigator", "researcher"}: # currently all roles can access this function
            for hash_md5 in hashes_md5:
                if get_object_by_md5_hash_db(hash_md5):
                    object = get_object_by_md5_hash_db(hash_md5)
                    current_authed_role = object['user_role_able_to_tag']
                    current_authed_role = list(set(current_authed_role) - set(remove_roles) - set(new_roles))
                    current_authed_role = current_authed_role + new_roles
                    object.update_one(
                        {"hash_md5": hash_md5},
                        {'$set': {'user_role_able_to_tag': list(current_authed_role)}}
                    )
                    result.append({'status': 'success', 'detail': hash_md5 + ' updated tag roles'})
                else:
                    result.append({'status': 'failure', 'detail': hash_md5 + ' not found'})
            return result
        return [{'status': 'failure', 'detail': username + ' not authorized'}]
    return [{'status': 'failure', 'detail': 'User does not exist'}]



# # ---------------------------
# # Video Database Interactions
# # ---------------------------


# def add_video_db(video: UniversalMLVideo):
#     """
#     Adds a new video to the database based on the UniversalMLVideo model.

#     :param video: UniversalMLVideo to add to database.
#     """

#     if not video_collection.find_one({"hash_md5": video.hash_md5}):
#         video_collection.insert_one(video.dict())


# def add_user_to_video(video: UniversalMLVideo, username: str):
#     """
#     Adds a user account to a UniversalMLVideo record. This is used to track which users upload videos.

#     :param v: UniversalMLVideo to update
#     :param username: Username of user who is accessing video
#     """
#     if video_collection.find_one({"hash_md5": video.hash_md5}):
#         existing_users = list(video_collection.find_one({"hash_md5": video.hash_md5})['users'])
#         if username not in existing_users:  # Only update if not in list already
#             existing_users.append(username)
#             video_collection.update_one(
#                 {"hash_md5": video.hash_md5},
#                 {'$set': {'users': existing_users}}
#             )


# def add_filename_to_video(video: UniversalMLVideo, filename: str):
#     """
#     Adds a filename to a UniversalMLVideo record. This is used to track all file names that an video is uploaded to
#     the server under. An video file is considered "the same" if their md5 hashes are identical.

#     :param video: UniversalMLVideo to update
#     :param filename: file name with extension
#     """
#     if video_collection.find_one({"hash_md5": video.hash_md5}):
#         current_names = list(video_collection.find_one({"hash_md5": video.hash_md5})['file_names'])
#         if filename not in current_names:  # Only update if not in list already
#             current_names.append(filename)
#             video_collection.update_one(
#                 {"hash_md5": video.hash_md5},
#                 {'$set': {'file_names': current_names}}
#             )


# def add_model_to_video_db(video: UniversalMLVideo, model_name, result):
#     """
#     Adds prediction data to a UniversalMLVideo object. This is normally called when a prediction microservice
#     returns data to the server with the results of a prediction request. The 'metadata' field is always updated.
#     in this method as a string to enable easy querying of nested model results.

#     :param video: UniversalMLVideo to add prediction data to
#     :param model_name: Name of model that was run on the video.
#     :param result: JSON results of the training
#     """

#     new_metadata = [list(video.dict()['models'].values()), model_name, result] + video.file_names
#     metadata_str = json.dumps(new_metadata)
#     for char_to_replace in ['"', "'", "\\", '[', ']', '{', '}']:
#         metadata_str = metadata_str.replace(char_to_replace, '')

#     video_collection.update_one({'hash_md5': video.hash_md5}, {'$set': {
#         'models.' + model_name: result,
#         'metadata': metadata_str
#     }})


# def get_videos_from_user_db(
#         username: str,
#         page: int = -1,
#         search_filter: dict = None,
#         search_string: str = '',
#         paginate: bool = True
# ):
#     """
#     Returns a list of video hashes associated with a username. This method also has pagination support and if a page
#     number is provided, then it will return dependency.PAGINATION_PAGE_SIZE video hashes. If the username of the user
#     in this request is an administrator, then all video in the server will be queried. Otherwise, only UniversalMLVideo
#     objects that contain the username will be included in the results.

#     This method also has unique functionality to allow for filtering of video results. If these values are provided,
#     the mongo query will be filtered based on the fields available in search_filter and search_string.

#     :param username: Username of user to get videos for
#     :param page: Page to return of results. Will return all videos if page is -1
#     :param search_filter Optional filter to narrow down query
#     :param search_string String that will be matched against video metadata
#     :param paginate Return all results or only page
#     :return: Array of video hashes, total pages
#     """

#     user = get_user_by_name_db(username)
#     if not user:  # If user does not exist, return empty
#         return [], 0

#     # If there is a filter, start with the correct dataset that has been filtered already
#     # Generate the result of the query in this step
#     if search_filter or search_string:
#         # List comprehension to take the inputted filter and make it into a pymongo query-compatible expression
#         search_params = []
#         if search_filter:  # Append search filter
#             flat_model_filter = (
#                 [{'models.' + model + '.' + str(model_class): {'$gt': 0}} for model in search_filter for model_class in
#                  search_filter[model]])
#             search_params.append({'$or': flat_model_filter})
#         if search_string:  # Append search string
#             search_params.append({"metadata": {'$regex': search_string, '$options': 'i'}})
#         if Roles.admin.name not in user.roles:  # Add username to limit results if not admin
#             search_params.append({'users': username})

#         result = video_collection.find({'$and': search_params}, {"hash_md5"})
#     else:
#         if Roles.admin.name in user.roles:
#             result = video_collection.find({}, {"hash_md5"})
#         else:
#             result = video_collection.find({'users': username}, {"hash_md5"})

#     # If we are getting a specific page of videos, then generate the list of hashes
#     final_hash_list = []
#     if page > 0 and paginate:
#         # We use this for actual db queries. Page 1 = index 0
#         page_index = page - 1
#         final_hash_list = result.skip(PAGINATION_PAGE_SIZE * page_index).limit(PAGINATION_PAGE_SIZE)

#         # After query, convert the result to a list
#         final_hash_list = [video_map['hash_md5'] for video_map in list(final_hash_list)]
#     elif not paginate:  # Return all results
#         final_hash_list = [video_map['hash_md5'] for video_map in list(result)]

#     num_videos = result.count()
#     return_value = {
#         "hashes": final_hash_list,
#         "num_videos": num_videos
#     }
#     if paginate:
#         return_value["num_pages"] = math.ceil(num_videos / PAGINATION_PAGE_SIZE)

#     return return_value


# def get_models_from_video_db(video: UniversalMLVideo, model_name: str = ""):
#     """
#     Creates a dictionary of all models with prediction results for a given video. This is returned
#     in the format of {modelName: result1, ...}.

#     :param video: UniversalMLVideo to obtain model results from
#     :param model_name: Optional filter to return specific model name
#     :return: Dictionary of model results
#     """

#     projection = {
#         "_id": 0,
#         "models": 1
#     }

#     if not video_collection.find_one({"hash_md5": video.hash_md5}):
#         return {}

#     if model_name != "":
#         results = video_collection.find_one({"hash_md5": video.hash_md5}, projection)
#         return {model_name: results['models'][model_name]}
#     else:
#         return video_collection.find_one({"hash_md5": video.hash_md5}, projection)['models']


# def get_video_by_md5_hash_db(video_hash) -> Union[UniversalMLVideo, None]:
#     """
#     Locates an video data by its md5 hash, and then creates a UniversalMLVideo object with that data.

#     :param video_hash: md5 hash of video to search for
#     :return: UniversalMLVideo object of video with a md5 hash, or None if not found
#     """
#     if not video_collection.find_one({"hash_md5": video_hash}):
#         return None

#     result = video_collection.find_one({"hash_md5": video_hash})
#     result.pop('_id')
#     return UniversalMLVideo(**result)


# def update_tags_to_video(hashes_md5: [str], username: str, remove_tags: [str], new_tags: [str]):
#     """
#     This method recieves two tags, where user can choose an tag and update it into a new tag

#     param:
#         username: user that is updating the tags
#     request body:
#         hashes_md5: list of md5 hashes
#         remove_tags: list of tags needs to be remove from videos, default []
#         new_tags: list of tags needs to be added to videos, default []
#     return:
#         always return a list with status message in it
#     """
#     result = []
#     user = get_user_by_name_db(username)
#     if user:
#         roles = user.roles
#         for hash_md5 in hashes_md5:
#             if video_collection.find_one({"hash_md5": hash_md5}):
#                 authed_roles = video_collection.find_one({"hash_md5": hash_md5})['user_role_able_to_tag']
#                 if set(roles) & set(authed_roles): # update tags here
#                     existing_tags = video_collection.find_one({"hash_md5": hash_md5})['tags']
#                     existing_tags = list(set(existing_tags) - set(remove_tags) - set(new_tags))
#                     existing_tags = existing_tags + new_tags
#                     video_collection.update_one(
#                     {"hash_md5": hash_md5},
#                     {'$set': {'tags': list(existing_tags)}}
#                     )
#                     result.append({'status': 'success', 'detail': hash_md5 + ' updated tags'})
#                 else:
#                     result.append({'status': 'failure', 'detail': hash_md5 + ' not authorized'})
#             else: # if video not found
#                 result.append({'status': 'failure', 'detail': hash_md5 + ' not found'})
#         return result
#     return [{'status': 'failure', 'detail': 'User does not exist'}]
   

# # TODO: Current any roles can change the user_role_able_to_tag field under video object, change the following mark line to limit access
# def update_role_to_tag_video(hashes_md5: [str], username: str, remove_roles: [str], new_roles: [str]):
#     """
#     Update new authorized tagging role to the UMI(video) object, so user with that role can
#     add or remove tag for that video

#     :param username: username of the current user
#     :request body:
#         hashes_md5: list of md5 hashes
#         remove_roles: list of roles needs to be remove from videos, default []
#         new_roles: list of roles needs to be added to videos, default []
#     """
#     result = []
#     user = get_user_by_name_db(username)
#     if user:
#         if set(user.roles) & {"admin", "investigator", "researcher"}: # currently all roles can access this function
#             for hash_md5 in hashes_md5:
#                 if video_collection.find_one({"hash_md5": hash_md5}):
#                     current_authed_role = video_collection.find_one({"hash_md5": hash_md5})['user_role_able_to_tag']
#                     current_authed_role = list(set(current_authed_role) - set(remove_roles) - set(new_roles))
#                     current_authed_role = current_authed_role + new_roles
#                     video_collection.update_one(
#                         {"hash_md5": hash_md5},
#                         {'$set': {'user_role_able_to_tag': list(current_authed_role)}}
#                     )
#                     result.append({'status': 'success', 'detail': hash_md5 + ' updated tag roles'})
#                 else:
#                     result.append({'status': 'failure', 'detail': hash_md5 + ' not found'})
#             return result
#         return [{'status': 'failure', 'detail': hash_md5 + ' not authorized'}]
#     return [{'status': 'failure', 'detail': 'User does not exist'}]


# # ---------------------------
# # Image Database Interactions
# # ---------------------------


# def add_image_db(image: UniversalMLImage):
#     """
#     Adds a new image to the database based on the UniversalMLImage model.

#     :param image: UniversalMLImage to add to database.
#     """

#     if not image_collection.find_one({"hash_md5": image.hash_md5}):
#         image_collection.insert_one(image.dict())


# def add_user_to_image(image: UniversalMLImage, username: str):
#     """
#     Adds a user account to a UniversalMLImage record. This is used to track which users upload images.

#     :param image: UniversalMLImage to update
#     :param username: Username of user who is accessing image
#     """
#     if image_collection.find_one({"hash_md5": image.hash_md5}):
#         existing_users = list(image_collection.find_one({"hash_md5": image.hash_md5})['users'])
#         if username not in existing_users:  # Only update if not in list already
#             existing_users.append(username)
#             image_collection.update_one(
#                 {"hash_md5": image.hash_md5},
#                 {'$set': {'users': existing_users}}
#             )


# def add_filename_to_image(image: UniversalMLImage, filename: str):
#     """
#     Adds a filename to a UniversalMLImage record. This is used to track all file names that an image is uploaded to
#     the server under. An image file is considered "the same" if their md5 hashes are identical.

#     :param image: UniversalMLImage to update
#     :param filename: file name with extension
#     """
#     if image_collection.find_one({"hash_md5": image.hash_md5}):
#         current_names = list(image_collection.find_one({"hash_md5": image.hash_md5})['file_names'])
#         if filename not in current_names:  # Only update if not in list already
#             current_names.append(filename)
#             image_collection.update_one(
#                 {"hash_md5": image.hash_md5},
#                 {'$set': {'file_names': current_names}}
#             )


# def add_model_to_image_db(image: UniversalMLImage, model_name, result):
#     """
#     Adds prediction data to a UniversalMLImage object. This is normally called when a prediction microservice
#     returns data to the server with the results of a prediction request. The 'metadata' field is always updated.
#     in this method as a string to enable easy querying of nested model results.

#     :param image: UniversalMLImage to add prediction data to
#     :param model_name: Name of model that was run on the image.
#     :param result: JSON results of the training
#     """

#     new_metadata = [list(image.dict()['models'].values()), model_name, result] + image.file_names
#     metadata_str = json.dumps(new_metadata)
#     for char_to_replace in ['"', "'", "\\", '[', ']', '{', '}']:
#         metadata_str = metadata_str.replace(char_to_replace, '')

#     image_collection.update_one({'hash_md5': image.hash_md5}, {'$set': {
#         'models.' + model_name: result,
#         'metadata': metadata_str
#     }})


# def get_images_from_user_db(
#         username: str,
#         page: int = -1,
#         search_filter: dict = None,
#         search_string: str = '',
#         paginate: bool = True
# ):
#     """
#     Returns a list of image hashes associated with a username. This method also has pagination support and if a page
#     number is provided, then it will return dependency.PAGINATION_PAGE_SIZE image hashes. If the username of the user
#     in this request is an administrator, then all images in the server will be queried. Otherwise, only UniversalMLImage
#     objects that contain the username will be included in the results.

#     This method also has unique functionality to allow for filtering of image results. If these values are provided,
#     the mongo query will be filtered based on the fields available in search_filter and search_string.

#     :param username: Username of user to get images for
#     :param page: Page to return of results. Will return all images if page is -1
#     :param search_filter Optional filter to narrow down query
#     :param search_string String that will be matched against image metadata
#     :param paginate Return all results or only page
#     :return: Array of image hashes, total pages
#     """

#     user = get_user_by_name_db(username)
#     if not user:  # If user does not exist, return empty
#         return [], 0

#     # If there is a filter, start with the correct dataset that has been filtered already
#     # Generate the result of the query in this step
#     if search_filter or search_string:
#         # List comprehension to take the inputted filter and make it into a pymongo query-compatible expression
#         search_params = []
#         if search_filter:  # Append search filter
#             flat_model_filter = (
#                 [{'models.' + model + '.' + str(model_class): {'$gt': 0}} for model in search_filter for model_class in
#                  search_filter[model]])
#             search_params.append({'$or': flat_model_filter})
#         if search_string:  # Append search string
#             search_params.append({"metadata": {'$regex': search_string, '$options': 'i'}})
#         if Roles.admin.name not in user.roles:  # Add username to limit results if not admin
#             search_params.append({'users': username})

#         result = image_collection.find({'$and': search_params}, {"hash_md5"})
#     else:
#         if Roles.admin.name in user.roles:
#             result = image_collection.find({}, {"hash_md5"})
#         else:
#             result = image_collection.find({'users': username}, {"hash_md5"})

#     # If we are getting a specific page of images, then generate the list of hashes
#     final_hash_list = []
#     if page > 0 and paginate:
#         # We use this for actual db queries. Page 1 = index 0
#         page_index = page - 1
#         final_hash_list = result.skip(PAGINATION_PAGE_SIZE * page_index).limit(PAGINATION_PAGE_SIZE)

#         # After query, convert the result to a list
#         final_hash_list = [image_map['hash_md5'] for image_map in list(final_hash_list)]
#     elif not paginate:  # Return all results
#         final_hash_list = [image_map['hash_md5'] for image_map in list(result)]

#     num_images = result.count()
#     return_value = {
#         "hashes": final_hash_list,
#         "num_images": num_images
#     }
#     if paginate:
#         return_value["num_pages"] = math.ceil(num_images / PAGINATION_PAGE_SIZE)

#     return return_value


# def get_models_from_image_db(image: UniversalMLImage, model_name: str = ""):
#     """
#     Creates a dictionary of all models with prediction results for a given image. This is returned
#     in the format of {modelName: result1, ...}.

#     :param image: UniversalMLImage to obtain model results from
#     :param model_name: Optional filter to return specific model name
#     :return: Dictionary of model results
#     """

#     projection = {
#         "_id": 0,
#         "models": 1
#     }

#     if not image_collection.find_one({"hash_md5": image.hash_md5}):
#         return {}

#     if model_name != "":
#         results = image_collection.find_one({"hash_md5": image.hash_md5}, projection)
#         return {model_name: results['models'][model_name]}
#     else:
#         return image_collection.find_one({"hash_md5": image.hash_md5}, projection)['models']


# def get_image_by_md5_hash_db(image_hash) -> Union[UniversalMLImage, None]:
#     """
#     Locates an image data by its md5 hash, and then creates a UniversalMLImage object with that data.

#     :param image_hash: md5 hash of image to search for
#     :return: UniversalMLImage object of image with a md5 hash, or None if not found
#     """
#     if not image_collection.find_one({"hash_md5": image_hash}):
#         return None

#     result = image_collection.find_one({"hash_md5": image_hash})
#     result.pop('_id')
#     return UniversalMLImage(**result)


# def update_tags_to_image(hashes_md5: [str], username: str, remove_tags: [str], new_tags: [str]):
#     """
#     This method recieves two tags, where user can choose an tag and update it into a new tag

#     param:
#         username: user that is updating the tags
#     request body:
#         hashes_md5: list of md5 hashes
#         remove_tags: list of tags needs to be remove from images, default []
#         new_tags: list of tags needs to be added to images, default []
#     return:
#         always return a list with status message in it
#     """
#     result = []
#     user = get_user_by_name_db(username)
#     if user:
#         roles = user.roles
#         for hash_md5 in hashes_md5:
#             if image_collection.find_one({"hash_md5": hash_md5}):
#                 authed_roles = image_collection.find_one({"hash_md5": hash_md5})['user_role_able_to_tag']
#                 if set(roles) & set(authed_roles): # update tags here
#                     existing_tags = image_collection.find_one({"hash_md5": hash_md5})['tags']
#                     existing_tags = list(set(existing_tags) - set(remove_tags) - set(new_tags))
#                     existing_tags = existing_tags + new_tags
#                     image_collection.update_one(
#                     {"hash_md5": hash_md5},
#                     {'$set': {'tags': list(existing_tags)}}
#                     )
#                     result.append({'status': 'success', 'detail': hash_md5 + ' updated tags'})
#                 else:
#                     result.append({'status': 'failure', 'detail': hash_md5 + ' not authorized'})
#             else: # if image not found
#                 result.append({'status': 'failure', 'detail': hash_md5 + ' not found'})
#         return result
#     return [{'status': 'failure', 'detail': 'User does not exist'}]
   

# # TODO: Current any roles can change the user_role_able_to_tag field under image object, change the following mark line to limit access
# def update_role_to_tag_image(hashes_md5: [str], username: str, remove_roles: [str], new_roles: [str]):
#     """
#     Update new authorized tagging role to the UMI(image) object, so user with that role can
#     add or remove tag for that image

#     :param username: username of the current user
#     :request body:
#         hashes_md5: list of md5 hashes
#         remove_roles: list of roles needs to be remove from images, default []
#         new_roles: list of roles needs to be added to images, default []
#     """
#     result = []
#     user = get_user_by_name_db(username)
#     if user:
#         if set(user.roles) & {"admin", "investigator", "researcher"}: # currently all roles can access this function
#             for hash_md5 in hashes_md5:
#                 if image_collection.find_one({"hash_md5": hash_md5}):
#                     current_authed_role = image_collection.find_one({"hash_md5": hash_md5})['user_role_able_to_tag']
#                     current_authed_role = list(set(current_authed_role) - set(remove_roles) - set(new_roles))
#                     current_authed_role = current_authed_role + new_roles
#                     image_collection.update_one(
#                         {"hash_md5": hash_md5},
#                         {'$set': {'user_role_able_to_tag': list(current_authed_role)}}
#                     )
#                     result.append({'status': 'success', 'detail': hash_md5 + ' updated tag roles'})
#                 else:
#                     result.append({'status': 'failure', 'detail': hash_md5 + ' not found'})
#             return result
#         return [{'status': 'failure', 'detail': hash_md5 + ' not authorized'}]
#     return [{'status': 'failure', 'detail': 'User does not exist'}]

# ---------------------------
# Model Database Interactions
# ---------------------------


def add_model_db(model_name: str, model_fields: List[str], model_type: str):
    """
    Adds information on the name and fields of a model to the model collection of the database. This is used when
    models register themselves to the server so that prediction requests know what fields to expect in the results.

    :param model_name: Name of model
    :param model_fields: List of all possible classes model may return
    :param model_type: Data type of model
    """
    if not model_collection.find_one({'model_name': model_name}):
        model_collection.insert_one({
            'model_name': model_name,
            'model_fields': model_fields,
            "model_data_type": model_type
        })


def get_models_db():
    """
    Creates a list of all registered models and their classes. The return value is of the format
    {modelName: [modelClass1, modelClass2, ...], ...}

    :return: List of all models and their classes. [] if no models registered.
    """
    all_models = list(model_collection.find())
    model_list = {model['model_name']: model['model_fields'] for model in all_models}
    return model_list


def get_models_db_by_type(data_type):
    """
    Creates a list of all registered models and their classes for a given data type. The return value is of the format
    {modelName: [modelClass1, modelClass2, ...], ...}

    :return: List of all models and their classes for that data type. [] if no models registered.
    """
    all_models = list(model_collection.find({"model_data_type":data_type}))
    model_list = {model['model_name']: model['model_fields'] for model in all_models}
    return model_list



# ------------------------------
# Training Database Interactions
# ------------------------------

def add_training_result_db(tr: TrainingResult):
    if not training_collection.find_one({'training_id': tr.training_id}):
        training_collection.insert_one(tr.dict())


def update_training_result_db(tr: TrainingResult):
    if not training_collection.find_one({'training_id': tr.training_id}):
        add_training_result_db(tr)
    else:
        training_collection.replace_one({'training_id': tr.training_id}, tr.dict())


def get_training_result_by_training_id(training_id: str):
    if not training_collection.find_one({'training_id': training_id}):
        return None

    res = training_collection.find_one({'training_id': training_id})

    return TrainingResult(**res)


def get_bulk_training_results_reverse_order_db(limit: int = -1, username: str = ''):
    """
    Gets the last <limit> results for submitted training requests. If a username is specified, it will find the last
    requests by that user, otherwise it will be system-wide.

    :param limit: Limit the number of training results (in descending order). If -1 will return all training results
    :param username: Optional username. If provided will only return training results user has submitted.
    :return: list of objects in the format of the TrainingResult.
    """

    query = {'username': username} if len(username) > 0 else {}
    if limit > 0:
        res = training_collection.find(query, {'_id': False}).sort([('$natural', -1)]).limit(limit)
    else:
        res = training_collection.find(query, {'_id': False}).sort([('$natural', -1)])

    return list(res)


def get_training_statistics_db(username: str = None):
    """
    Query the database for information on the number of jobs pending and completed.

    :param username: Optional username. If provided will only find jobs that a user has submitted.
    :return: 2-tuple of jobs pending, jobs finished
    """
    if username is not None:
        u = get_user_by_name_db(username)
        finished = training_collection.find({'username': username, 'complete': True})
        pending = training_collection.find({'username': username, 'complete': False})
    else:
        finished = training_collection.find({'complete': True})
        pending = training_collection.find({'complete': False})

    return pending.count(), finished.count()
