import time

def init():
    """
    This method will be run once on startup. You should check if the supporting files your
    model needs have been created, and if not then you should create/fetch them.
    """
    time.sleep(1)



def predict(prediction_input: str):
    """
    Interface method between model and server. This signature must not be
    changed and your model must be able to create a prediction from the image
    file or text that is passed in.

    Depending on the model type as defined in model/config.py, this method will receive a different input:

    'image'  :  Model receives a file name to an image file, opens it, and creates a prediction
    'text'   :  Model receives a string of text and uses it to create a prediction.


    Note: All images are stored in the directory '/app/images/' in the Docker container. You may assume that the file
    name that is passed to this method is valid and that the image file exists.

    Example code for opening the image using PIL:
    image = Image.open('/app/images/'+image_file_name)
    """

    return {
        'classes': ['POSITIVE', 'NEGATIVE'],  # List every class in the classifier
        'result': {  
            'POSITIVE': 1
        }
    }

