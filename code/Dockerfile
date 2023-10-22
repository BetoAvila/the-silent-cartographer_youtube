FROM ubuntu:latest

RUN apt-get update -y && apt-get upgrade
RUN apt-get install -y wget build-essential software-properties-common
RUN wget https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz
RUN tar -xzf Python-3.12.0.tgz
RUN ./Python-3.12.0/configure --enable-optimizations
RUN make /Python-3.12.0/install-sh

