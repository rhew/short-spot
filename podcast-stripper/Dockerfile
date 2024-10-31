FROM python:3

WORKDIR /usr/src/app
ADD stripper.py .
ADD ffmpeg_util.py .
ADD openai_util.py .
ADD requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update
RUN apt-get install ffmpeg -y

RUN pip install pyasyncore
# Allow installation to fail when building locally
RUN pip install audioop-lts; exit 0

ENV PYTHONUNBUFFERED=1

CMD [ "python", "./stripper.py" ]

