FROM python:3.12-slim
ENV LANG=C.UTF-8
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install \
    nano -y
RUN mkdir /root/sc_yt && \
    cd /root/sc_yt
WORKDIR /root/sc_yt
COPY . .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
RUN --mount=type=secret,id=yt_api_key \
    cat /run/secrets/yt_api_key >> /root/sc_yt/.env
# CMD [ "python", "function.py" ]