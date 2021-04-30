import base64
import time
import cv2


def init():
    """
    This method will be run once on startup. You should check if the supporting files your
    model needs have been created, and if not then you should create/fetch them.
    """

    # Placeholder init code. Replace the sleep with check for model files required etc...
    global __model
    __model = 1
    time.sleep(1)


def predict(prediction_object_path):
    """
    Interface method between model and server. This signature must not be
    changed and your model must be able to create a prediction from the object
    file that is passed in.

    Depending on the model type as defined in model/config.py, this method will receive a different input:

    'object'  :  Model receives a file name to an image file, opens it, and creates a prediction
    'text'   :  Model receives a string of text and uses it to create a prediction.


    Note: All objects are stored in the directory '/app/objects/' in the Docker container. You may assume that the file
    path that is passed to this method is valid and that the image file exists.

    prediction_object_path will be in the form: "app/objects/file_name", where file_name is the video, image, etc. file.
    """

    cap = cv2.VideoCapture(prediction_object_path)
    
    return {
        'classes': ['isGreen', 'isRed'],  # List every class in the classifier
        'result': {  # For results, use the class names above with the result value
            'isGreen': 0,
            'isRed': __model  # Note that we reference the variable we used in init(). This will be returned as 1.
        }
    }
