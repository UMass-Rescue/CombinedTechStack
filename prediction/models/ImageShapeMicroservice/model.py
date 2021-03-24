from PIL import Image
import time


def init():
    """
    This method will be run once on startup. You should check if the supporting files your
    model needs have been created, and if not then you should create/fetch them.
    """

    # Placeholder init code. Replace the sleep with check for model files required etc...
    return True

def predict(image_file_name):
    """
    Interface method between model and server. This signature must not be
    changed and your model must be able to predict given a file-like object
    with the image as an input.
    """

    image = Image.open('/app/images/'+image_file_name)

    width, height = image.size

    image.close()

    return {
        'classes': ['width', 'height'],  # List every class in the classifier
        'result': {  # For results, use the class names above with the result value
            'height': height,
            'width': width,
        }
    }
