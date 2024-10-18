FROM python:3

WORKDIR /usr/src/app
ADD stripper.py .
ADD requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update
RUN apt-get install ffmpeg -y

RUN pip install pyasyncore
RUN pip install audioop-lts

ENV PYTHONUNBUFFERED=1

CMD [ "python", "./stripper.py" ]

