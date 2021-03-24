# Model Directory

This directory is populated by the specific model folder from the ../../models directory at runtime by Docker. This allows for each worker to only 
access the specific model files it needs without giving it all of the models that are available.