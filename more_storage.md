# Docker Storage Help

The images created by the **Combined Tech Stack** takes up approximately 30 GB. By default on Windows, Docker Desktop with WSL2 will download the images into a specified folder in the user's main drive. (usually C:). If a user has a secondary drive with a lot more space (like I did), it is useful to be able to store all images in that drive instead. Below we will detail the process. 

## Step 1: 
Make sure your Docker is shut down. Shut down your docker desktop by right click on the Docker Desktop icon and select Quit Docker Desktop

## Step 2:
Go to any folder on your main drive using the CLI (command line). And use the command: 
``` 
wsl --list -v
```
Which displays should display two lines: "docker-desktop" and "docker-desktop-data".

From the same folder run: 
```
wsl --export docker-desktop-data "docker-desktop-data.tar"
```
which will install "docker-desktop-data.tar" into the folder you are curerntly in.

## Step 3:
Then unregister docker-desktop-data from wsl, note that after this, your ext4.vhdx file would automatically be removed (so back it up first if you have important existing image/container):

```
wsl --unregister docker-desktop-data
```

## Step 4:
Import the docker-desktop-data back to wsl, but now the ext4.vhdx would reside in different drive/directory:

```
wsl --import docker-desktop-data "your/drive/here" "docker-desktop-data.tar" --version 2
```

Start the Docker Desktop again and it should work

You may delete the "docker-desktop-data.tar" file (NOT the ext4.vhdx file) if everything looks good for you after verifying

[SOURCE](https://stackoverflow.com/questions/62441307/how-can-i-change-the-location-of-docker-images-when-using-docker-desktop-on-wsl2)
