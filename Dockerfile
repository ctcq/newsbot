FROM python:latest

ADD ./* /
RUN pip install --no-cache-dir -r ./requirements.txt

CMD [ "python", "/app/main.py" ]