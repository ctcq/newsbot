FROM python:3

ENV RESOURCES_FOLDER "/opt/newsfeed_bot/resources"

ADD . /opt/newsfeed_bot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python /opt/newsfeed_bot/src/main.py --resources" + ${RESOURCES_FOLDER} ]