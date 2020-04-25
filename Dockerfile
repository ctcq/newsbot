FROM python:latest

RUN apt-get update && apt-get install -y curl ffmpeg pocketsphinx libasound2-dev libpulse-dev python-sphinxbase swig

# Update pip
RUN python -m pip install --upgrade pip setuptools wheel

COPY ./requirements.txt /
RUN pip install --no-cache-dir -r ./requirements.txt

# Install english model files for deepspeech
RUN mkdir /opt/deepspeech
WORKDIR /opt/deepspeech/
RUN curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.7.0/deepspeech-0.7.0-models.pbmm
    && curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.7.0/deepspeech-0.7.0-models.scorer


COPY . /
CMD [ "python", "/app/main.py" ]