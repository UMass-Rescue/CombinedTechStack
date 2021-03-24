from PIL import Image
import time
from model.scene_detect_model import SceneDetectionModel

model = None


def init():
    """
    This method will be run once on startup. You should check if the supporting files your
    model needs have been created, and if not then you should create/fetch them.
    """

    global model

    print('Loading SceneDetection model')

    model = SceneDetectionModel()

    print('SceneDetection model loaded')


def predict(image_file_name):
    """
    Interface method between model and server. This signature must not be
    changed and your model must be able to predict given a file-like object
    with the image as an input.
    """

    global model

    if model is None:
        raise RuntimeError("SceneDetection model is not loaded properly")

    model.load_image('/app/images/'+image_file_name)
    scene_detect_result = model.predict_scene()

    return {
        'classes': ['confidence', 'scene_attributes', 'environment_type'],  # List every class in the classifier
        'result': {  # For results, use the class names above with the result value
            'confidence': scene_detect_result['category_results'],
            'scene_attributes': scene_detect_result['attributes_result'],
            'environment_type': scene_detect_result['environment']
        }
    }
