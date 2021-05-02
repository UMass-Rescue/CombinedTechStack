import os
import json
from model.model import predict, init
from model.config import model_name, model_type
from pymongo import MongoClient

client = MongoClient(os.getenv('DB_HOST', default='database'), 27017)
database_object_collection = client['server_database']['objects']
database_model_collection = client['server_database']['models']


def predict_object(object_hash, prediction_obj):
    try:
        result = predict(prediction_obj)  # Create prediction on model
    except Exception as e:
        # Do not send prediction results to server on crash.
        print(e)
        print('[Error] Model Prediction Crash. Model: [' + model_name + '] Hash:[' + object_hash + ']', flush=True)
        return

    print('Prediction Complete', result, flush=True)

    # Update model results in the database
    current_image_obj = database_object_collection.find_one({"hash_md5": object_hash})
    if current_image_obj:
        nm = [list(current_image_obj['models'].values()), model_name, result['result']] + current_image_obj['file_names']
        metadata_str = json.dumps(nm)
        for char_to_replace in ['"', "'", "\\", '[', ']', '{', '}']:
            metadata_str = metadata_str.replace(char_to_replace, '')

        database_object_collection.update_one({'hash_md5': object_hash}, {'$set': {
            'models.' + model_name: result['result'],
            'metadata': metadata_str
        }})

    # Add model structure to server database.
    if not database_model_collection.find_one({'model_name': model_name}):
        database_model_collection.insert_one({
            'model_name': model_name,
            'model_fields': result['classes'],
            'model_type': model_type
        })
