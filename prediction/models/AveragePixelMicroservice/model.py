from PIL import Image
from PIL.ImageStat import Stat
import time


def init():
    """
    This method will be run once on startup. You should check if the supporting files your
    model needs have been created, and if not then you should create/fetch them.
    """

    # Placeholder init code. Replace the sleep with check for model files required etc...
    time.sleep(1)


def predict(image_file_name):
    """
    Interface method between model and server. This signature must not be
    changed and your model must be able to predict given a file-like object
    with the image as an input.
    """

    image = Image.open('/app/images/'+image_file_name)
    stat = Stat(image)
    av_r = stat.mean[0]
    av_g = stat.mean[1]
    av_b = stat.mean[2]

    image.convert('L')  # Convert to grayscale
    stat = Stat(image)
    brightness = stat.mean[0]  # Between 0 -> 255. 0 is DARK and 255 is LIGHT

    image.close()
    return {
        'classes': ['average_red', 'average_green', 'average_blue', 'brightness'],  # List every class in the classifier
        'result': {  # For results, use the class names above with the result value
            'average_red': av_r,
            'average_green': av_g,
            'average_blue': av_b,
            'brightness': stat.mean[0]
        }
    }
