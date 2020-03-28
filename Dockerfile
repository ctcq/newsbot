FROM python:3

ENV RESOURCES_FOLDER=${RESOURCES_FOLDER}

ADD . /opt/newsfeed_bot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python /opt/newsfeed_bot/src/main.py --resources" + ${RESOURCES_FOLDER} ]