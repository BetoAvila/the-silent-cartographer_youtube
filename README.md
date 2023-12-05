# 1. The Silent Cartographer: YouTube
## 1.1. Introduction

This program analyzes video comments on YouTube for sentiment analysis using Llama 2.
On this way, one can observe and measure viewers engagement and interaction like a watch tower and hence the Halo-referenced name.

![alt text](./tower.jpg "Silent Cartographer")

---
- [1. The Silent Cartographer: YouTube](#1-the-silent-cartographer-youtube)
  - [1.1. Introduction](#11-introduction)
- [2. Description](#2-description)
  - [2.1. In a nutshell](#21-in-a-nutshell)
- [3. Prerequisites](#3-prerequisites)
- [4. Architecture](#4-architecture)
  - [4.1. YouTube API](#41-youtube-api)
  - [4.2. Docker](#42-docker)
    - [4.2.1. Docker secrets](#421-docker-secrets)
    - [4.2.2. Miniconda and PyTorch](#422-miniconda-and-pytorch)
  - [4.3. Llama2](#43-llama2)
  - [4.4. Resulting Docker image](#44-resulting-docker-image)

# 2. Description
## 2.1. In a nutshell
Given a YouTube video URL, the program grabs its comments using YouTube's API, then analyzes them using Llama 2 and classifies them in 3 categories according to their content as **Positive, Negative and Neutral**. Finally, it returns a data set containing comments' evaluation and information about the video and commenters. Since this is a containerized project, it can be executed anywhere using Docker.

# 3. Prerequisites
1. [Python](https://www.python.org) version 3.11.5 is implemented here using Miniconda.
2. [Docker](https://www.docker.com) to run this program anywhere.
3. [Anaconda](https://www.anaconda.com)'s minimalist version Miniconda to create an environment for PyTorch without unused packages.
4. [PyTorch](https://www.pytorch.org) since Llama 2 was developed with this framework.
5. [Llama2](https://ai.meta.com/llama/) Meta's Large Language Model to power analysis and evaluation.
6. llama-cpp, this is a tough cookie I'll describe later but in summary it allows us to easily manipulate Llama 2 instances. So many thanks for the awesome work of [Georgi Gerganov's repo](https://github.com/ggerganov/llama.cpp) to allows us to quantize and reduce the model and [Andrei's repo](https://github.com/abetlen/llama-cpp-python) who created the binding of the quantized model. Again, more on this later.

# 4. Architecture
## 4.1. YouTube API
To start this app, YouTube API access is needed to programmatically extract and manipulate video comments data, to get this access follow these [steps](https://developers.google.com/youtube/v3/getting-started) to get an API key. To more efficiently use this API, install [`google-api-python-client`](https://pypi.org/project/google-api-python-client/) it will prompt for the API key acquired in the previous step.

The docs about YouTube API usage are great and I could not recommend them more, feel free to read them [here]( https://developers.google.com/youtube/v3/docs).

## 4.2. Docker
Docker setup consists of a base miniconda3 image with a few more layers. The [`Dockerfile`](./code/Dockerfile) was designed to be as simple as possible and to delegate most of the installations to the [`startup.sh`](./code/startup.sh) file. This is the second most important function the Dockerfile has, the first one is to safely store and manage YouTube API key since the program needs it.

### 4.2.1. Docker secrets
The latest version of Docker allows us to handle credentials or sensitive data by [mounting a secret]( https://docs.docker.com/engine/reference/builder/#run---mounttypesecret). This is different from creating a secret which is implemented only on swarm mode. In summary mounting secrets:
- Allows the container to access credentials without baking them into the image.
- Credentials are not revealed in the logs even in full history logs.
- There is no need to store credentials as plain text or in a repo (these should only be store in a password manager).
- Works even if credentials file (such as `.env`) is included in `.dockerignore` file. Including credentials file in the `.dockerignore` file is crucial to properly work with Docker.
The command included in the Dockerfile is:

```
RUN --mount=type=secret,id=yt_api_key \
    cat /run/secrets/yt_api_key >> /home/sc_yt/.env
```

The first line creates the secret in the default location `/run/secrets/yt_api_key` and the second line creates a `.env` file with the contents of the secret and places it in the working directory `/home/sc_yt`, note that this secret-mounting command allows us to manipulate the secret only in the context of the `RUN` instruction, hence the creation of the new credential file has to be done in the same instruction. This basically safely copies the content of my local `.env` file which looks like this:

```
YT_API_KEY=my_youtube_api_key
```

to an exact same new file inside the container despite the `.dockerignore` file prevents Docker from copying it from the local path:

```
######## dockerignore file ########
# Files
.dockerignore
.env

# Folders

```

This is implemented during **`image build`** with the command:

```
docker buildx build -t sc_yt_img --no-cache --secret id=yt_api_key,src=.env .
```

which lets Docker know where is the `.env` credentials file with the `--secret` flag and `src` parameter.

### 4.2.2. Miniconda and PyTorch
The [Miniconda Docker image](https://hub.docker.com/r/continuumio/miniconda3) is used as it is the easiest way to properly install PyTorch and the needed requirements. After previous step of mounting the secret, the `Dockerfile` executes the instruction 

```
RUN ./startup.sh
```

which in turns executes the contents of the [`startup.sh`](./code/startup.sh) file. The 3 main parts of it are:
-	Update of the linux kernel and installation of building essentials.
-	Installation of Python requirements with pip and a [`requirements.txt`](./code/requirements.txt) file.
-	Proper installation of PyTorch with conda to leverage GPU resources.

Delegating setup and installations with a different file of Dockerfile, keeps the Dockerfile clean, simple and reusable in other projects.

## 4.3. Llama2
Llama 2 is offered in multiple sizes:
-	7 billion parameters with 13 Gb in size, great to chat and summarize, fast.
-	13 billion parameters with 26 Gb in size, great to answer questions (although questionable in my opinion), it takes its time to respond.
-	 70 billion parameters with 100 Gb + in size, awesome for creative tasks, slow in response.

The app I implemented is done with the 7b chat-optimized version transformed and quantized for its local usage. Oversimplifying (probably inaccurately), to transform is to enable its use with C++ architecture, which significantly increases its response speed; and to quantize is to decrease the floating point precision for the same purpose, after these 2 processes I end up using the model ` ggml-model-q4_0.gguf `.

These 2 processes are done with [Georgi Gerganov's repo](https://github.com/ggerganov/llama.cpp) and a great tutorial is [this]( https://www.youtube.com/watch?v=TsVZJbnnaSs), thanks Alex for this awesome video.

To create the python bindings please follow instructions described in [Andrei's repo](https://github.com/abetlen/llama-cpp-python), this enables an easy-to-program pythonic control.

Unfortunately, these steps are quite complex and hence simply mentioned in this documentation, please take your time to go through them thoroughly as they are needed to generate the `ggml-model-q4_0.gguf` model.

## 4.4. Resulting Docker image
After following the prior steps, the files to build the image result as follows (although in the final image the `.dockerignore` file is excluded):

```
/code
    .dockerignore
    .env
    Dockerfile
    requirements.txt
    startup.sh
    function.py
    ggml-model-q4_0.gguf
```

Finally, to run a container with the image run:

```
docker run -it --rm sc_yt_img /bin/bash
```

This runs the container in interactive mode and allows execution of commands or modifications of code with nano.

