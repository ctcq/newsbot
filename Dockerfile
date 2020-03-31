FROM python:latest

ADD . /opt/newsfeed_bot
WORKDIR /opt/newsfeed_bot
RUN pip install --no-cache-dir -r ./requirements.txt
CMD [ "python", "./src/main.py" ]