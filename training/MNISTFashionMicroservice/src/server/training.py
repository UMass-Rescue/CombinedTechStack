import os
import tempfile
import shutil
import requests
import sys
import logging
import json

from src.server.dependency import ModelData
import tensorflow as tf

class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    Source: https://stackoverflow.com/a/39215961
    """
    def __init__(self, logger, level):
       self.logger = logger
       self.level = level
       self.linebuf = ''

    def write(self, buf):
       for line in buf.rstrip().splitlines():
          self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass

def train_model(training_id, model_data: ModelData):

    """
    Train model(s) based on a given model and hyperparameters
    Now supporting two hyperparameters which are 
    - Optimizer and learning_rate
    """

    # SET LOGGER TO PRINT TO STDOUT AND WRITE TO FILE
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("/log/{}.log".format(training_id)),
            logging.StreamHandler(sys.stdout)
        ]
    )
    log = logging.getLogger('foobar')
    sys.stdout = StreamToLogger(log,logging.INFO)
    sys.stderr = StreamToLogger(log,logging.ERROR)
    
    # get API KEY from the environment file
    API_KEY = os.getenv('API_KEY')

    best_acc = -1
    best_val_acc = -1

    best_loss = -1
    best_val_loss = -1
    best_model = None
    best_config = None
    best_optimizer = None
    best_loss_fn = None
    # print("Save:" + str(model_data.save))
    logging.info("Save:" + str(model_data.save))
    try:
        # print('[Training] Starting to train model ID: ' + training_id)
        logging.info('[Training] Starting to train model ID: ' + training_id)

        dataset_root = '/app/src/public_dataset'

        img_height = 28
        img_width = 28

        train_ds = tf.keras.preprocessing.image_dataset_from_directory(
            dataset_root,
            validation_split=model_data.split,
            subset="training",
            seed=model_data.seed,
            image_size=(img_height, img_width),
            batch_size=model_data.batch_size
        )

        validation_ds = tf.keras.preprocessing.image_dataset_from_directory(
            dataset_root,
            validation_split=model_data.split,
            subset="validation",
            seed=model_data.seed,
            image_size=(img_height, img_width),
            batch_size=model_data.batch_size
        )

        autotune_buf_size = tf.data.AUTOTUNE

        train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=autotune_buf_size)
        validation_ds = validation_ds.cache().prefetch(buffer_size=autotune_buf_size)

        optimizer_dict = model_data.optimizer.dict()
        config = {}
        if "config" in optimizer_dict and optimizer_dict["config"]:
            # convert all float config from string to float
            convert_data_type(optimizer_dict["config"])
            config = optimizer_dict["config"]

        # if learning_rate is not defined, it will use the optimizor's default value 
        learning_rate_list = [None]
        if model_data.optimizer.learning_rate:
            learning_rate_list = model_data.optimizer.learning_rate

        # get loss function object
        loss_dict = model_data.loss_function.dict()
        if loss_dict["config"] is None:
            loss_dict["config"] = {}
        else:
            convert_data_type(loss_dict["config"])

        loss_fn = tf.keras.losses.get(loss_dict)
        logging.info(loss_fn)

        # create all hyperparameters combination
        optimizer_class = model_data.optimizer.dict()
        hyperparameters = [[o,lr] for o in optimizer_dict["class_name"]
                                  for lr in learning_rate_list]

        # loop through all hyperparameters
        for hp in hyperparameters:
            # load model from json file
            model = tf.keras.models.model_from_json(model_data.model_structure)

            optimizer_obj = {
                "class_name": hp[0],
                "config": config
            }
            # set learning rate if not None
            if hp[1]:
                optimizer_obj["config"]["learning_rate"] = hp[1]

            optimizer = tf.keras.optimizers.get(optimizer_obj)

            n_epochs = model_data.n_epochs

            # train the model
            (acc, val_acc, loss, val_loss, model) = fit(model, loss_fn, optimizer, train_ds, validation_ds, n_epochs)

            # CHECK FOR THE BEST MODEL (from validation accuracy)
            if val_acc > best_val_acc:
                best_acc = acc
                best_val_acc = val_acc
                best_loss = loss
                best_val_loss = val_loss
                best_model = model
                best_optimizer = optimizer.get_config()
                best_loss_fn = loss_fn.get_config()

            # END LOOP

        logging.info('[Training] Completed training on model ID: ' + training_id)

        # If we are saving the model, we must save it to folder, zip that folder,
        # and then send the zip file to the server via HTTP requests
        if model_data.save:
            # print('[Training] Preparing to save Model data on model ID: ' + training_id)
            logging.info('[Training] Preparing to save Model data on model ID: ' + training_id)

            # Create temp dir and save model to it
            tmpdir = tempfile.mkdtemp()
            model_save_path = os.path.join(tmpdir, training_id)

            # Save model nested 1 more layer down to facilitate unzipping
            tf.saved_model.save(best_model, os.path.join(model_save_path, training_id))

            shutil.make_archive(model_save_path, 'zip', model_save_path)

            print(tmpdir)

            files = {'model': open(model_save_path+'.zip', 'rb')}
            requests.post(
                'http://host.docker.internal:' + str(os.getenv('SERVER_PORT')) + '/training/model',
                headers={'api_key': API_KEY},
                params={'training_id': training_id},
                files=files 
            )

            # print('[Training] Sent SavedModel file data on model ID: ' + training_id)
            logging.info('[Training] Sent SavedModel file data on model ID: ' + training_id)


    except:
        # print('[Training] Critical error on training: ' + training_id)
        logging.exception('[Training] Critical error on training: ' + training_id)


    result = {
        'training_accuracy': best_acc,
        'validation_accuracy': best_val_acc,
        'training_loss': best_loss,
        'validation_loss': best_val_loss,
        'optimizer_config': str(best_optimizer),
        'loss_config': str(best_loss_fn)
    }

    logging.info('[Training] results: ' + str(result))

    # Send HTTP request to server with the statistics on this training
    r = requests.post(
        'http://host.docker.internal:' + str(os.getenv('SERVER_PORT')) + '/training/result',
        headers={'api_key': API_KEY},
        json={
            'dataset_name': os.getenv('DATASET_NAME'),
            'training_id': training_id,
            'results': result
        })
    r.raise_for_status()

    # print("[Training Results] Sent training results to server.")
    logging.info("[Training Results] Sent training results to server.")

def fit(model, loss_fn, optimizer, train_ds, validation_ds, n_epochs):

    acc = [-1]
    val_acc = [-1]

    loss = [-1]
    val_loss = [-1]

    logging.info(loss_fn)
    logging.info(optimizer)

    model.compile(optimizer=optimizer,
                  loss=loss_fn,
                  metrics=['accuracy'])

    logging.info('[Training] with optimizer config: ' + str(model.optimizer.get_config()))
    logging.info('[Training] with loss function config: ' + str(model.loss.get_config()))

    history = model.fit(train_ds, validation_data=validation_ds, epochs=n_epochs)

    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']

    loss = history.history['loss']
    val_loss = history.history['val_loss']


    return (acc[-1], val_acc[-1], loss[-1], val_loss[-1], model)

def convert_data_type(input_dict):
    for k, v in input_dict.items():
        if v == "True": 
            input_dict[k] = True
        elif v == "False":
            input_dict[k] = False
        elif isfloat(v):
            input_dict[k] = float(v)


def isfloat(value):
    if type(value) == bool:
        return False
    try:
        float(value)
        return True
    except ValueError:
        return False


