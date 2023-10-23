FROM ubuntu:latest
ENV LANG=C.UTF-8
RUN apt-get update -y && apt-get upgrade
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata nano
RUN apt-get install software-properties-common build-essential libbz2-dev libsqlite3-dev libssl-dev pkg-config software-properties-common wget zlib1g-dev -y
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update -y && apt-get upgrade
RUN apt-get install python3.12 -y
RUN cd /tmp && wget https://bootstrap.pypa.io/get-pip.py && python3.12 get-pip.py
RUN mkdir /usr/local/sc_yt && cd /usr/local/sc_yt
WORKDIR /usr/local/sc_yt
COPY . .
RUN pip3.12 install -r requirements.txt

