import pytest

from routers import prediction, training

from dependency import api_key_collection, UniversalMLImage
from db_connection import get_user_by_name_db, get_api_keys_by_user_db, add_image_db
from main import app
from routers.auth import create_testing_account, create_testing_keys
from routers.auth import (
    get_current_user,
    current_user_investigator,
    current_user_researcher,
    current_user_admin,
)


@pytest.fixture(scope="session", autouse=True)
def test_configuration():
    create_testing_account()  # Ensure testing account is created
    create_testing_keys()  # Ensure API keys are created

    # Override all permissions to return the testing user object. This allows us to bypass the OAuth2 authentication
    app.dependency_overrides[get_current_user] = override_logged_in_user
    app.dependency_overrides[current_user_investigator] = override_logged_in_user
    app.dependency_overrides[current_user_researcher] = override_logged_in_user
    app.dependency_overrides[current_user_admin] = override_logged_in_user
    app.dependency_overrides[prediction.get_api_key] = override_api_key_prediction
    app.dependency_overrides[training.get_api_key] = override_api_key_training
    # image1 = UniversalMLImage(**{
    #             'file_names': ['test_image_file_1.png'],
    #             'hash_md5': 'image1hash',
    #             'users': ['testing'],
    #             'models': {},
    #             'tags': [],
    #             'user_role_able_to_tag': ['admin']
    #         })
    # add_image_db(image1)

    yield

    api_key_collection.delete_many({'user': 'testing'})  # Delete all API keys created during testing


def override_logged_in_user():
    return get_user_by_name_db("testing")

def override_api_key_prediction():
    return get_api_keys_by_user_db(get_user_by_name_db('api_key_testing'))[0]

def override_api_key_training():
    return get_api_keys_by_user_db(get_user_by_name_db('api_key_testing'))[1]
