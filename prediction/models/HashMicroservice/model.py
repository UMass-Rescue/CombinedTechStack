import hashlib
import imagehash
from PIL import Image
import time


def init():
    """
    This method will be run once on startup. You should check if the supporting files your
    model needs have been created, and if not then you should create/fetch them.
    """

    return True  # Nothing to init


def predict(image_file_name):
    """
    Interface method between model and server. This signature must not be
    changed and your model must be able to predict given a file-like object
    with the image as an input.
    """

    image = Image.open('/app/objects/'+image_file_name)

    md5 = hashlib.md5(image.tobytes()).hexdigest()
    sha1 = hashlib.sha1(image.tobytes()).hexdigest()
    perceptual = str(imagehash.phash(image))

    return {
        'classes': ['md5', 'sha1', 'perceptual'],  # List every class in the classifier
        'result': {  # For results, use the class names above with the result value
            'md5': md5,
            'sha1': sha1,
            'perceptual': perceptual,
        }
    }
