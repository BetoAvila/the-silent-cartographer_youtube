FROM ubuntu:22.04
ENV LANG=C.UTF-8
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install \
    nano \
    software-properties-common \
    wget -y
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get install python3.12 -y
RUN cd /tmp && \
    wget https://bootstrap.pypa.io/get-pip.py && \
    python3.12 get-pip.py
RUN mkdir /usr/local/sc_yt && cd /usr/local/sc_yt
WORKDIR /usr/local/sc_yt
COPY . .
RUN pip3.12 install -r requirements.txt
RUN --mount=type=secret,id=yt_api_key \
    cat /run/secrets/yt_api_key >> /usr/local/sc_yt/.env
# CMD [ "python3.12", "function.py" ]
