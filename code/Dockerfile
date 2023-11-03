FROM continuumio/miniconda3
ENV LANG=C.UTF-8
RUN mkdir /home/sc_yt && \
    cd /home/sc_yt
WORKDIR /home/sc_yt
COPY . .
RUN --mount=type=secret,id=yt_api_key \
    cat /run/secrets/yt_api_key >> /home/sc_yt/.env
RUN chmod +x startup.sh 
RUN ./startup.sh