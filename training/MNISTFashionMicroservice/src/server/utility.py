import os
import tensorflow as tf

from keras_preprocessing.image import ImageDataGenerator
from shutil import copyfile

from src.server.dependency import logger, dataset_settings


def setup_dataset():
    dataset_root = '/app/src/dataset/'
    symlink_root = '/app/src/public_dataset/'
    extensions_found = set()

    logger.debug('Starting Dataset Init.')

    classes = next(os.walk(dataset_root))[1]
    total_count = 0
    copy_images = len(os.listdir(symlink_root)) <= 1  # Must check >1 to account for .DS_Store on Mac

    for imageClass in classes:
        dataset_folder = dataset_root + imageClass + '/'
        public_dataset_folder = symlink_root + imageClass + '/'
        counter = 0

        if not os.path.isdir(public_dataset_folder):
            os.mkdir(public_dataset_folder)

        for dirpath, dirs, files in os.walk(dataset_folder):
            for f in files:
                file_name, file_extension = os.path.splitext(f)
                if file_extension.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
                    extensions_found.add(file_extension)
                    if copy_images:
                        copyfile(dirpath + f, public_dataset_folder + str(counter) + file_extension)
                    counter += 1
                    total_count += 1

    logger.debug('Finished Dataset Init.')

    dataset_settings.classes = classes
    dataset_settings.num_images = total_count
    dataset_settings.extensions = extensions_found
