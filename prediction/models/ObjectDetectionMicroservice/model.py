from PIL import Image
import time, json
from torchvision import models, transforms
import torch

model = None
label_map = {}
super_COCO_classes ={}
classes = []
result = {}
score_threshold = 0.6

def init():
    """
    This method will be run once on startup. You should check if the supporting files your
    model needs have been created, and if not then you should create/fetch them.
    """
    # Placeholder init code. Replace the sleep with check for model files required etc...
    #load FasterRCNN model using ResNet trained on COCO
    global model, label_map, super_COCO_classes, classes, result, score_threshold

    USE_GPU = True
    if USE_GPU and torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')

    model = models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
    model.eval()
    #read classes
    labels = open('model/coco_labels.txt', 'r')
    for line in labels:
        ids = line.split(',')
        label_map[int(ids[0])] = ids[2]
    # read super classes from json file
    with open('model/coco_labels_super.json', 'r') as fp:
        temp = json.load(fp)
    #changing keys to ',' separated labels to single labels
    for k in temp:
        class_labels = k.split(',')
        classes.append(temp[k])
        result[temp[k]] = 0
        for label in class_labels:
            if label not in super_COCO_classes:
                super_COCO_classes[label] = temp[k]
            else:
                super_COCO_classes[label] += ', '+ temp[k]


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

    global model, label_map, super_COCO_classes, classes, result, score_threshold
    for key in result:
        result[key] = 0
    image = Image.open('/app/images/' + prediction_input)
    image_tensor = transforms.functional.to_tensor(image)

    output = model([image_tensor])
    for i in range(len(output)):
        scores = output[i]['scores'].tolist()
        # boxes = output[i]['boxes'].tolist()
        labels = output[i]['labels'].tolist()
        
        for index, score in enumerate(scores):
            if score > score_threshold:
                label = label_map[labels[index]].strip() #remove leading and trailing spaces if any
                if label in super_COCO_classes:
                    result[super_COCO_classes[label]] += 1
                


    return {
        'classes': classes,  # List every class in the classifier
        'result': result # For results, use the class names above with the result value            
    }