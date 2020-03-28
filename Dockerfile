FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r repuirements.txt

COPY . .

CMD [ "python", "./main.py"]