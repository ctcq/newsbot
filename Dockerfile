FROM python:latest

RUN pip install --no-cache-dir -r ./requirements.txt

ADD ./src /app
ADD ./resources /resources

CMD [ "python", "/app/main.py" ]