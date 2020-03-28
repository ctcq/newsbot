FROM python:3

ADD . /opt/newsfeed_bot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "src/main.py"]