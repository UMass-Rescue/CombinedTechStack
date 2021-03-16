# MLDatasetTemplate

## Overview

This is a template application for hosting a dataset and allowing machine learning models to be trained on the data
without developers getting access to the actual contents of the dataset. The MLDatesetTemplate has an integrated
webserver which allows for controlled actions between the client and this dataset. This server allows for the
template work with a server such as [\[This One\]](https://github.com/UMass-Rescue/PhotoAnalysisServer)

The entire application is containerized with Docker, so the development and
deployment process is portable and platform agnostic.


## Initial Setup

To run this application, there are some commands that must be run. All of these should be
done via the command line in the root directory of the project folder.

Ensure that you have Docker running on your computer before attempting these commands.


### Configure Application

When serving a dataset with this template, there are some options that must be configured before
you can get full functionality. These options are set configured once during setup, and will
not need to be changed in the future during development.

#### [Configuration] Step 1
Open the file `.env` in the root directory. Change the first line from:
`DATASET_NAME=sample_dataset` to a more descriptive name.

> [**Example**]
> If your dataset contains faces, the first line of your `.env` file may look like the following:
> ```text
> DATASET_NAME=face_dataset
> ```

#### [Configuration] Step 2
Open the file `.env` in the root directory. Change the second line to contain the path
to the dataset on your computer

> [**Example**]
> If your dataset is stored in the `Faces` folder located at `~/Documents/Datasets/Faces`, then 
> set the line in `.env` to
> ```text
> DATASET_LOCATION=~/Documents/Datasets/Faces
> ```

#### [Configuration] Step 3 (Optional)
This step must only be done if the dataset is hosted on the same computer as other MLDatasetTemplates or
MLMicroserviceTemplates.

Open the file `.env` in the root directory. Change the line from:
`PORT=6005` to another port that you have not already used.

#### [Configuration] Step 4 (Optional)
This step must only be completed if the template is connected to the server, and if the server is using a
non-default port.

Open the file `.env` in the root directory. Change the line from:
`SERVER_PORT=5000` to another port that you have not already used.

#### [Configuration] Step 5 (Optional)
You must only complete this step if the MLDatasetTemplate will be connected to a server.
Open the file `secrets.py` file in the root directory. On the server, generate a new API key.
Assuming our example API key is `abcde12345`, change:
```python
API_KEY = 'paste_your_api_key_here'
```
to
```python
API_KEY = 'abcde12345'
```


### Build and Run Application

Once you have configured the template, you must run these commands to build and run the model.

**As mentioned above, all of these commands must be run in the root directory of the project.**


#### [Build & Run] Step 1
Download dependencies with Docker and build container

```cmd
docker-compose build
```

#### [Build & Run] Step 2
Start application
```cmd
docker-compose up -d
```

---