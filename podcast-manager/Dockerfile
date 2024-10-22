FROM python:3

WORKDIR /usr/src/app
ADD manage-feeds.py .
ADD config.py .
ADD requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD [ "python", "./manage-feeds.py" ]

