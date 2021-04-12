import pytest
from fastapi.testclient import TestClient
import glob
from main import app
from fastapi import Depends
from db_connection import get_user_by_name_db

from main import app

client = TestClient(app)

# --------------
# Working Tests
# --------------

@pytest.mark.timeout(5)
def test_register_model():

    # create mlmicroservice object. 
    # MLMicroserviceTemplate needs to be running on port that mlservice template is running on
    # can be changed once we have a monorepo
    mlmicroservice_object={"name": "testing_register", "socket": "http://host.docker.internal:5005"}

    # Predict on images
    register_model = client.post("/model/register", json=mlmicroservice_object)
    assert register_model.status_code == 200


# ---------
# Image Tagging test
# ----------
# @pytest.mark.timeout(5)
# def test_tag_add():
#     response = client.post("/model/tag/update",
#     json = {"md5_hashes": ["image1hash"],
#     "remove_tags": [],
#     "new_tags": ["bar", "foo"]
#     })
#     image_response = client.post('/model/results', data = {'md5_hashes': ['image1hash']})
#     assert image_response.json()['detail']
#     assert "bar" in image_response[0].tags
#     assert response.status_code == 200


# @pytest.mark.timeout(5)
# def test_tag_delete():
#     response = client.post("/model/tag/role/update",
#     json = {"md5_hashes": ["image1hash"],
#     "remove_tags": ["bar"],
#     "new_tags": []
#     })
#     image_response = client.post('/model/results', data = ['image1hash'])
#     assert "foo" in image_response.json()[0]['tags']
#     assert "bar" not in image_response.json()[0]['tags']
#     assert response.status_code == 200


# @pytest.mark.timeout(5)
# def test_tag_role_add():
#     response = client.post("/model/tag/role/update",
#     json = {"md5_hashes": ["image1hash"],
#     "remove_roles": ['researcher']
#     })
#     image_response = client.post('/model/results', data = ['image1hash'])
#     assert "researcher" in image_response.json()[0]['user_role_able_to_tag']
#     assert "admin" in image_response.json()[0]['user_role_able_to_tag']
#     assert response.status_code == 200


# @pytest.mark.timeout(5)
# def test_tag_role_delete():
#     response = client.post("/model/tag/role/update",
#     json = {"md5_hashes": ["image1hash"],
#     "remove_roles": ['researcher']
#     })
#     image_response = client.post('/model/results', data = ['image1hash'])
#     assert "researcher" not in image_response.json()[0]['user_role_able_to_tag']
#     assert "admin" in image_response.json()[0]['user_role_able_to_tag']
#     assert response.status_code == 200
    
    
# --------------
# Failing Tests
# --------------

# from https://fastapi.tiangolo.com/advanced/testing-dependencies/
# not clear if this is needed (come back after monorepo is created)
#
# async def override_dependency():
#     return get_user_by_name_db('testing')

# app.dependency_overrides[current_user_investigator] = override_dependency

# @pytest.mark.timeout(5)
# def test_get_all_prediction_models():

#     # Predict on images
#     # needs dependency?
#     register_model = client.post("/model/all")
#     assert register_model.status_code == 200

# @pytest.mark.timeout(5)
# def test_predict_on_images():

#     #read files from docker container (add file path)
#     upload_files = [(file, open(file), "image/jpeg") for file in glob.glob("/app/<file_path>/*")]

#     #pass arguments
#     args= {"images":upload_files, 
#             "models":["example_model"]
#     }

#     # Predict on images
#     predict_on_images = client.post("/model/predict", params=args)
#     print("STATUS", predict_on_images)
#     assert predict_on_images.status_code == 200

    
