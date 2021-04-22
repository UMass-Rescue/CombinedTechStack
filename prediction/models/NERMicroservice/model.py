from PIL import Image
import time
from transformers import pipeline


def init():
    """
    This method will be run once on startup. You should check if the supporting files your
    model needs have been created, and if not then you should create/fetch them.
    """
    # Placeholder init code. Replace the sleep with check for model files required etc...
    # global nlp 
    # nlp = pipeline("ner")
    time.sleep(1)


def predict(prediction_input):
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
    nlp = pipeline("ner")
    text_input = prediction_input  # If text model
    # image = Image.open('/app/images/' + prediction_input)  # If image model

    only_person = False
    result_dict = {}
    for entity in ['I-PER', 'I-LOC', 'I-ORG', 'I-MISC']:
        result_dict[entity] = ''
    
    result = nlp(text_input)
    res = result[0]
    s = text_input[res['start']: res['end']]
    curr_index = res['index']
    curr_entity = res['entity']

    i = 1
    while(True):
        while i < len(result) and curr_index+1 == result[i]['index'] and curr_entity == result[i]['entity']:
            
            s += text_input[result[i]['start']: result[i]['end']]
            curr_index = result[i]['index']
            i += 1
        if not only_person or (only_person and curr_entity == 'I-PER'):
            # print(s, " ", curr_entity)
            result_dict[curr_entity] += ' ' + s
        if i == len(result):
            break
        s = text_input[result[i]['start']: result[i]['end']]
        curr_index = result[i]['index']
        curr_entity = result[i]['entity']
        i+=1

    return {
        'classes': ['PER', 'LOC', 'ORG', 'MISC'],  # List every class in the classifier
        'result': {  # For results, use the class names above with the result value
            'PER': result_dict['I-PER'],
            'LOC': result_dict['I-LOC'],
            'ORG': result_dict['I-ORG'],
            'MISC': result_dict['I-MISC']
        }
    }