# Give a name to describe this model. The name should conform to python variable naming conventions, and should be
# only a single word.
model_name = 'object_detection'

# Tags are used to describe the performance of a model. These simple keywords can help people decide whether your model
# is appropriate to use for their situation. Some examples of tags are 'fast', 'accurate', or 'essential'. You should
# limit the number of tags your model has to only contain a few with relevant information.
model_tags = ['FasterRCNN', 'COCO', 'PyTorch']


# The model type determines what inputs your model will receive. The options are:
# - 'image'  :  Model receives a file name to an image file, opens it, and creates a prediction
# - 'text'   :  Model receives a string of text and uses it to create a prediction.
model_type = 'image'
