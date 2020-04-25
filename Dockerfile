FROM python:latest

RUN apt-get update && apt-get install -y ffmpeg pocketsphinx libasound2-dev libpulse-dev python-sphinxbase swig

# Update pip
RUN python -m pip install --upgrade pip setuptools wheel

COPY ./requirements.txt /
RUN pip install --no-cache-dir -r ./requirements.txt

COPY . /
CMD [ "python", "/app/main.py" ]