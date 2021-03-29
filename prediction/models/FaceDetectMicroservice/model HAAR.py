import os.path
from os import path
import urllib.request
import cv2
from src.server.dependency import logger


"""

This is the default facial detection for OpenCV. Its kinda bad and not very impressive

This is left here for reference but is not in use.

"""

# Cascade filepath
local_cascade_filepath = 'src/model/frontalface_default_cascade.xml'

def init():
    """
    This method will be run once on startup. You should check if the supporting files your
    model needs have been created, and if not then you should create/fetch them.
    """

    # Where cascade XML file is hosted

    frontalface_default_cascade_url = 'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml'

    if not path.exists(local_cascade_filepath):
        urllib.request.urlretrieve(frontalface_default_cascade_url, local_cascade_filepath)
        logger.debug('Cascade file has been downloaded.')
    else:
        logger.debug('Cascade file already downloaded.')

def predict(image_file):
    """
    Interface method between model and server. This signature must not be
    changed and your model must be able to predict given a file-like object
    with the image as an input.
    """

    
    face_cascade = cv2.CascadeClassifier(local_cascade_filepath)  # Cascade
    
    image = cv2.imread(image_file.name)
    
    image_grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Must make grayscale
    
    faces = face_cascade.detectMultiScale(image_grayscale, 1.2, 4)

    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 0), 2)

    cv2.imwrite('src/image.jpg', image)

    return {
        'classes': ['number_faces'],  
        'result': { 
            'number_faces': len(faces),
        }
    }
