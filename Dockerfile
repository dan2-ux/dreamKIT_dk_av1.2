FROM python:3.11-bookworm

WORKDIR /app

COPY data.csv define.json fine_vector.py model1.3.py model_requirement.txt  /app/

ENV UNAME=sdv-runtime

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --yes pulseaudio-utils

# Set up the user
RUN export UNAME=$UNAME UID=1000 GID=1000 && \
    mkdir -p "/home/${UNAME}" && \
    echo "${UNAME}:x:${UID}:${GID}:${UNAME} User,,,:/home/${UNAME}:/bin/bash" >> /etc/passwd && \
    echo "${UNAME}:x:${UID}:" >> /etc/group && \
    mkdir -p /etc/sudoers.d && \
    echo "${UNAME} ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/${UNAME} && \
    chmod 0440 /etc/sudoers.d/${UNAME} && \
    chown ${UID}:${GID} -R /home/${UNAME} && \
    gpasswd -a ${UNAME} audio

RUN apt-get update \
    && apt-get install -y libportaudio2 libportaudiocpp0 portaudio19-dev \
    && apt install -y alsa-utils libasound2 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip \
    && pip install -r model_requirement.txt \
    && pip install https://github.com/KittenML/KittenTTS/releases/download/0.1/kittentts-0.1.0-py3-none-any.whl \
    && pip install sounddevice \ 
    && pip install pygame \
    && pip install gtts

RUN chown -R 1000:1000 /app

COPY pulse-client.conf /etc/pulse/client.conf

CMD bash -c "pulseaudio --start & python3 model1.3.py"
