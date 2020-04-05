FROM python:latest

ADD ./requirements.txt /
RUN pip install --no-cache-dir -r ./requirements.txt

ADD . /newsbot
CMD [ "python", "/newsbot/app/main.py /newsbot/app/resources /newsbot/app/data" ]