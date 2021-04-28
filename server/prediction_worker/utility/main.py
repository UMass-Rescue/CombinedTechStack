import os
import json
from model.model import predict, init
from model.config import model_name, model_type
from pymongo import MongoClient

client = MongoClient(os.getenv('DB_HOST', default='database'), 27017)
database_image_collection = client['server_database']['images']
database_model_collection = client['server_database']['models']


def predict_image(image_hash, image_file_name):
    try:
        result = predict(image_file_name)  # Create prediction on model
    except:
        # Do not send prediction results to server on crash.
        print('[Error] Model Prediction Crash. Model: [' + model_name + '] Hash:[' + image_hash + ']', flush=True)
        return

    # Update model results in the database
    current_image_obj = database_image_collection.find_one({"hash_md5": image_hash})
    if current_image_obj:
        nm = [list(current_image_obj['models'].values()), model_name, result['result']] + current_image_obj['file_names']
        metadata_str = json.dumps(nm)
        for char_to_replace in ['"', "'", "\\", '[', ']', '{', '}']:
            metadata_str = metadata_str.replace(char_to_replace, '')

        database_image_collection.update_one({'hash_md5': image_hash}, {'$set': {
            'models.' + model_name: result['result'],
            'metadata': metadata_str
        }})

    # Add model structure to server database.
    if not database_model_collection.find_one({'model_name': model_name}):
        database_model_collection.insert_one({
            'model_name': model_name,
            'model_fields': result['classes']
        })
