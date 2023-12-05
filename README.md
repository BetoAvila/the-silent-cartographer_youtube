# 1. The Silent Cartographer: YouTube
## 1.1. Introduction

This program analyzes video comments on YouTube for sentiment analysis using Llama 2.
On this way, one can observe and measure viewers engagement and interaction like a watch tower and hence the Halo-referenced name.

![alt text](./imgs/tower.jpg "Silent Cartographer")

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
  - [4.3. Llama 2](#43-llama-2)
  - [4.4. Resulting Docker image](#44-resulting-docker-image)
- [5. Usage](#5-usage)
  - [5.1. Logic discussion](#51-logic-discussion)
  - [5.2. Llama 2 prompting](#52-llama-2-prompting)
  - [5.3. Final results](#53-final-results)
  - [5.4. Running the code locally](#54-running-the-code-locally)
- [6. Conclusions](#6-conclusions)
- [7. Further work](#7-further-work)


# 2. Description
## 2.1. In a nutshell
Given a YouTube video URL, the program grabs its comments using YouTube's API, then analyzes them using Llama 2 and classifies them in 3 categories according to their content as **Positive, Negative and Neutral**. Finally, it returns a data set containing comments' evaluation and information about the video and commenters. Since this is a containerized project, it can be executed anywhere using Docker.

![alt text](./imgs/silet_cartographer_yt.png 'diagram')

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

The docs about YouTube API usage are great and I could not recommend them more, feel free to read them [here]( https://developers.google.com/youtube/v3/docs) or read [this version](https://developers.google.com/resources/api-libraries/documentation/youtube/v3/python/latest/index.html) which is more detailed. The docs about Python client for YT API can be found [here](https://github.com/googleapis/google-api-python-client/blob/main/docs/start.md).

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

## 4.3. Llama 2
Llama 2 is offered in multiple sizes:
-	7 billion parameters with 13 Gb in size, great to chat and summarize, fast.
-	13 billion parameters with 26 Gb in size, great to answer questions (although questionable in my opinion), it takes its time to respond.
-	 70 billion parameters with 100 Gb + in size, awesome for creative tasks, slow in response.

The app I implemented is done with the 7b chat-optimized version transformed and quantized for its local usage. Oversimplifying (probably inaccurately), to transform is to enable its use with C++ architecture, which significantly increases its response speed; and to quantize is to decrease the floating point precision for the same purpose, after these 2 processes I end up using the model ` ggml-model-q4_0.gguf `.

These 2 processes are done with [Georgi Gerganov's repo](https://github.com/ggerganov/llama.cpp) and a great tutorial is [this]( https://www.youtube.com/watch?v=TsVZJbnnaSs), thanks Alex for this awesome video.

To create the python bindings please follow instructions described in [Andrei's repo](https://github.com/abetlen/llama-cpp-python), this enables an easy-to-code pythonic control.

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

Finally, to run a container use command `docker run`. This command will need a few more parameters to properly generate the results which are discussed below.

# 5. Usage
## 5.1. Logic discussion

As shown in the [description](#2-description) diagram, this app queries YT’s API to list all top comments on a video given its URL in the form `https://www.youtube.com/watch?v=xxxxxxxxx`. This is possible with the API key discussed above and safely stored in the container as a `.env` file.

Please consider a top comment is the comment initially written by a viewer and excluding following comments replying to this initial one. 

While listing these comments, the API query requests these features: `'video_id', 'comment_id', 'textOriginal', 'authorDisplayName', 'authorChannelUrl', 'likeCount', 'publishedAt', 'updatedAt'` thus having more information about the commenter.

This process is iterative as it will request as much comment data as there is in 100 comments per API request batches. Although this has a credit usage on YT API, discussing and managing API credit usage is beyond the scope of this app.

## 5.2. Llama 2 prompting

Once comment data is placed locally, Llama 2 will read each comment and decide if it is a positive, negative, or neutral comment. This is defined by using words or phrases that exhibit these sentiments. In the case of neutral comments like questions or simple observations, Llama 2 will also tell apart these cases.

Prompting this LLM is not too sophisticated, it simply consists of an instruction letting Llama 2 to classify comments based on its content, without any fancy terms, suffixes or prompt engineering tricks. This has proven to work more than acceptably in the several cases tested.

## 5.3. Final results

The results are summarized in a `.csv` file containing the following columns:

| Feature            | Datatype     |
| ------------------ | ------------ |
| video_id           | str          |
| comment_id         | str          |
| comment            | str          |
| comment_author     | str          |
| author_url         | str          |
| comment_like_count | int          |
| published_at       | datetime(tz) |
| updated_at         | datetime(tz) |
| AI_evaluation      | str          |

This file will be stored in the container running the application, with the name `result_{datetime_of_execution}_{yt_video_url}.csv` so it is easier to keep track of multiple executions of this app.

## 5.4. Running the code locally

Summarizing the Docker image creation we start with:
1.	Miniconda3 base Docker image.
2.	Install pip dependencies (check [`requirements.txt`](./code/requirements.txt) file).
3.	Install PyTorch with conda manager.
4.	Execute docker build command discussed in section [4.2.1. Docker secrets](#421-docker-secrets): 
```
docker buildx build -t sc_yt_img --no-cache --secret id=yt_api_key,src=.env . 
```
The above define and create the Docker image for this app.

Then we instantiate the image with a container with the following command (note the container will be deleted after we exit its shell, remove `--rm` flag if this is not a wanted behaviour):
```
docker run -it --rm sc_yt_img /bin/bash
```
This will start the container and places us in the home directory from where we can execute the following command:
```
python function.py ‘https://www.youtube.com/watch?v=xxxxxxxxx’ ‘eng’
```
This makes the shell use the python environment to execute the program `function.py` using the YouTube video defined with `‘https://www.youtube.com/watch?v=xxxxxxxxx’` (note the quotation marks as they are crucial) using English language to analyze the comments. Using this, one can analyze any video of any length in YouTube in either English or Spanish languages.

This command should finish in a few seconds or minutes depending on the computing resources of the machine running the container, internet speed and running processes on the computer. Confirmation message should be similar to this:
```
Finished analyzing video comments and results are summarized in the file: {csv_name}
```
From there we can copy the results file into the local machine with `docker cp` command or store it in a DB, or something else.

# 6. Conclusions
These are some points I want to stress:
-	This runs on any machine. From a supercomputer to a RaspberryPI, thanks to Docker and as long as you have a valid YT API key anyone could use this, Meta is also open source and free to use in almost any scale.
-	This safely stores your API key. This was one of the most important issues to solve as it would have been quite inconvenient to have an AI powered tool without a safe password storage. This method could also be used with DockerHub as no sensitive information is ever exposed.
-	This is quite flexible. LLMs allows us to create as far as our imagination lets us and this is the simplest of uses for an AI.
-	This can help marketing teams a lot. Using this tool can leverage insights on interaction, relevance, and impact in social networks.
-	This is somewhat scalable. The current state of this app allows to instantiate multiple containers to analyze more than one YT vide at once, but certainly this may have its limitations and challenges.

# 7. Further work

This was huge: understatement. But a few tweaks can be done:

-	Instead of making Llama 2 read comments one by one, we could make it read them at once and respond with multiple assessments in the same prompt. This should be designed in a way that we don’t exceed the context and token limits.
-	There should be a way to tag already processed comments, so no duplication of work occurs.
-	A very interesting and more challenging option would be to make the LLM reply all comments, or reply based on the comment’s content. This would leverage user engagement and interaction; this would increase consumer behaviour knowledge too.
-	Thinking big, a video summary table should also be included with features like id, publishedAt, title, description, duration, viewCount, likeCount, dislikeCount.
-	Scaling up is always a big issue, but I believe it could be achieved with an API, thus separating data ingestion, data engineering and AI parts moving towards a microservices architecture.
-	Docker provides an instruction called `ENTRYPOINT`, it makes containers executable and produces a bit faster execution, but despite this scenario was tested it was not successful.
