import os
import tempfile
import shutil
import requests
import sys
import logging

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

    acc = [-1]
    val_acc = [-1]

    loss = [-1]
    val_loss = [-1]
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

        model = tf.keras.models.model_from_json(model_data.model_structure)

        loss_fn = tf.keras.losses.get(model_data.loss_function.dict())
        logging.info(loss_fn)


        optimizer_dict = model_data.optimizer.dict()
        # optimizer_dict = [dict([a, int(x)] for a, x in model_data.optimizer.dict().items())]
        if "config" in optimizer_dict:
            optimizer_dict["config"].update((k, float(v)) for k, v in optimizer_dict["config"].items() if isfloat(v))

        optimizer = tf.keras.optimizers.get(optimizer_dict)
        logging.info(optimizer)

        model.compile(optimizer=optimizer,
                      loss=loss_fn,
                      metrics=['accuracy'])

        history = model.fit(train_ds, validation_data=validation_ds, epochs=model_data.n_epochs)

        acc = history.history['accuracy']
        val_acc = history.history['val_accuracy']

        loss = history.history['loss']
        val_loss = history.history['val_loss']
        # print('[Training] Completed training on model ID: ' + training_id)
        logging.info('[Training] Completed training on model ID: ' + training_id)

        API_KEY = os.getenv('API_KEY')

        # If we are saving the model, we must save it to folder, zip that folder,
        # and then send the zip file to the server via HTTP requests
        if model_data.save:
            # print('[Training] Preparing to save Model data on model ID: ' + training_id)
            logging.info('[Training] Preparing to save Model data on model ID: ' + training_id)

            # Create temp dir and save model to it
            tmpdir = tempfile.mkdtemp()
            model_save_path = os.path.join(tmpdir, training_id)

            # Save model nested 1 more layer down to facilitate unzipping
            tf.saved_model.save(model, os.path.join(model_save_path, training_id))

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
        'training_accuracy': acc[-1],
        'validation_accuracy': val_acc[-1],
        'training_loss': loss[-1],
        'validation_loss': val_loss[-1]
    }

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

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

def hyperparameter_tuning(training_id, model_data: ModelData):
    pass

