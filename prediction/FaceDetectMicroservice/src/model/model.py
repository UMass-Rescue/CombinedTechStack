from matplotlib import pyplot
from matplotlib.patches import Rectangle
from mtcnn.mtcnn import MTCNN
from src.server.dependency import logger
from PIL import Image
from fastapi import File, UploadFile


"""

Facial detection using Multi-Task Cascaded Convolutional Neural Network

Reference:
https://machinelearningmastery.com/how-to-perform-face-detection-with-classical-and-deep-learning-methods-in-python-with-keras/ 
https://arxiv.org/ftp/arxiv/papers/1604/1604.02878.pdf

"""

def init():
    """
    This method will be run once on startup. You should check if the supporting files your
    model needs have been created, and if not then you should create/fetch them.
    """

    logger.debug('Nothing to init...')


def predict(image_file_name):
    """
    Interface method between model and server. This signature must not be
    changed and your model must be able to predict given a file-like object
    with the image as an input.
    """

    image = Image.open('/app/src/images/'+image_file_name)

    def draw_image_with_boxes(result_list):
        # load the image
        data = pyplot.imread(image)
        # plot the image
        pyplot.imshow(data)
        # get the context for drawing boxes
        ax = pyplot.gca()
        # plot each box
        for result in result_list:
            # get coordinates
            x, y, width, height = result['box']
            # create the shape
            rect = Rectangle((x, y), width, height, fill=False, color='red')
            # draw the box
            ax.add_patch(rect)
        # show the plot
        pyplot.savefig('src/image.jpg')

    pixels = pyplot.imread(image)

    # create the detector, using default weights
    detector = MTCNN()
    # detect faces in the image
    faces = detector.detect_faces(pixels)

    # For debug, un comment this method to generate image showing faces detected
    draw_image_with_boxes(faces)

    # logger.debug(faces)

    return {
        'classes': ['number_faces'],  
        'result': { 
            'number_faces': len(faces),
        }
    }
