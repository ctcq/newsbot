FROM python:latest

ADD ./requirements.txt /
RUN pip install --no-cache-dir -r ./requirements.txt

ADD . /
CMD [ "python", "/app/main.py ./resources ./data" ]