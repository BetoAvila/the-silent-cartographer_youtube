#!/bin/sh

# Update, upgrade and installations
apt-get update -y && \
apt-get upgrade -y && \
apt-get install \
nano build-essential -y

# python dependencies
pip install --upgrade pip
pip install -r requirements.txt
conda install pytorch -c pytorch -y