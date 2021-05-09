from transformers import pipeline

#nlp = None

def init():
    """
    This method will be run once on startup. You should check if the supporting files your
    model needs have been created, and if not then you should create/fetch them.
    """
    global nlp
    nlp = pipeline("sentiment-analysis")
    return



def predict(prediction_input: str):
    """
    Interface method between model and server. This signature must not be
    changed and your model must be able to create a prediction from the image
    file or text that is passed in.

    Depending on the model type as defined in model/config.py, this method will receive a different input:

    'image'  :  Model receives a file name to an image file, opens it, and creates a prediction
    'text'   :  Model receives a string of text and uses it to create a prediction.


    Note: All images are stored in the directory '/app/objects/' in the Docker container. You may assume that the file
    name that is passed to this method is valid and that the image file exists.

    Example code for opening the image using PIL:
    image = Image.open('/app/objects/'+image_file_name)
    """
    global nlp
    data = str(prediction_input)
    result = nlp(data)[0]

    return {
        'classes': ['POSITIVE', 'NEGATIVE'],  # List every class in the classifier
        'result': {  
            result["label"]: result["score"]
        }
    }

