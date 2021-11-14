FROM python:latest

RUN apt-get update && apt-get install -y curl

# Update pip
RUN python -m pip install --upgrade pip setuptools wheel

COPY ./requirements.txt /
RUN pip install --no-cache-dir -r ./requirements.txt

COPY . /
CMD [ "python", "/app/main.py", "/resources" ]
