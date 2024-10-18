#!/usr/bin/env python

import datetime
from glob import glob
import json
import tempfile
import os
import pickle

import click
from openai import OpenAI
from pydub import AudioSegment
import pyinotify


def srt_format(timestamp):
    return datetime.datetime.strftime(
        datetime.datetime.fromtimestamp(timestamp), "%H:%M:%S,%f")[:-3]


def get_commercials(client, transcript):
    # TODO Bobby: use "structured outputs" Aug 6 model
    prompt = """Analyze the following SRT transcript of a podcast episode to
        identify commercial segments. Commercial segments are typically
        introduced by a break or change in topic, often followed by
        sponsorship mentions. For each commercial:

        - Identify the sponsor of the commercial (company name).
        - Determine which lines of the transcript the commercial spans.
        - Output the sponsor and the start and end line numbers of each
          commercial segment.

        Use JSON. Example format:

        [
            {"sponsor": "Some Company",
             "start_line": 77,
             "end_line": 80},
            {"sponsor": "Some Other Company",
             "start_line": 103,
             "end_line": 111}
        ]
        """

    messages = [
        {
            "role": "user",
            "content": (f"{line} {srt_format(segment.start)}"
                        + f"--> {srt_format(segment.end)} {segment.text}")
        } for line, segment in enumerate(transcript.segments)
    ]
    messages.insert(0, {"role": "system", "content": prompt})

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    # trim non-json from the front
    json_string = completion.choices[0].message.content[
        completion.choices[0].message.content.index('['):]

    # handle non-json in the end
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        return json.loads(json_string[:e.pos])


def get_sponsor(client, company):
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=f"Sponsored by {company}.",
    )

    response.stream_to_file("output.mp3")


def get_trimmed(client, audio_file, transcript, commercial_data):
    original = AudioSegment.from_mp3(audio_file)
    trimmed = AudioSegment.empty()
    end_commercial_index = 0
    for commercial in commercial_data:
        # TODO: make sure times ascend
        start_time = transcript.segments[commercial['start_line']].start
        end_time = transcript.segments[commercial['end_line']].end

        if start_time*1000 < end_commercial_index:
            raise IndexError("List of commercials must be sequential.")

        print(f"{int(end_time - start_time)} second message "
              + f"from {commercial['sponsor']} "
              + f"at {srt_format(start_time)} to {srt_format(end_time)}.")

        trimmed += original[end_commercial_index:start_time*1000]

        # add the sponsor name
        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="onyx",
            input=f"This podcast is sponsored by, {commercial['sponsor']}.",
            response_format='mp3'
        ) as response:
            with tempfile.NamedTemporaryFile(delete=False) as fp:
                fp.close()
                response.stream_to_file(fp.name)
                trimmed += AudioSegment.from_mp3(fp.name)

        end_commercial_index = end_time*1000
    trimmed += original[end_commercial_index:]
    return trimmed


def reduce_audio_file(filename):
    max_size = 26339874
    reduced = AudioSegment.from_mp3(filename)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        fp.close()
    reduced.export(fp.name, format="mp3", parameters=["-ac", "1"])
    reduced_size = os.path.getsize(fp.name)
    frame_rate = reduced.frame_rate
    while reduced_size >= max_size:
        print(f'reduced_size is {reduced_size} bytes.')
        frame_rate = int(frame_rate/2)
        reduced.export(fp.name, format="mp3", parameters=["-ac", "1", "-ab", f'{frame_rate}'])
        print(f'Reduced frame rate to {frame_rate}.')
        reduced_size = os.path.getsize(fp.name)
    print(f"Reduced input file by {os.path.getsize(filename)-reduced_size} "
          + f"to {reduced_size} before transcribing.")
    return fp.name


def get_transcript(client, filename, load=False):
    if not load:
        reduced_filename = reduce_audio_file(filename)
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            prompt="",
            response_format="verbose_json",
            file=open(reduced_filename, "rb")
        )
        with open('transcript.pickle', 'wb') as f:
            pickle.dump(transcript, f, pickle.HIGHEST_PROTOCOL)
    else:
        print("Loading previous transcript.")
        with open('transcript.pickle', 'rb') as f:
            transcript = pickle.load(f)

    return transcript


def strip(client, path, output, load=False):
    print(f'Starting {os.path.basename(path)} -> {os.path.basename(output)}')
    transcript = get_transcript(client, path, load)
    commercials = get_commercials(client, transcript)
    get_trimmed(
        client, path, transcript, commercials
    ).export(output, format="mp3")


def get_stripped_name(path):
    if path.endswith('-stripped.mp3'):
        raise ValueError(f'mp3 path already stripped: {path}')

    if path.endswith('.mp3'):
        return f'{path[:-4]}-stripped.mp3'

    raise ValueError(f'Invalid mp3 path for adding stripped name: {path}')


def strip_all(client, directory):
    print(f'Stripping everything in {directory}')
    for filename in glob(os.path.join(directory, '*', '*.mp3')):
        filepath = os.path.join(directory, filename)

        if filepath.endswith('-stripped.mp3'):
            print(f'ignoring {filename}')
            continue

        try:
            stripped_name = get_stripped_name(filepath)

            if os.path.isfile(stripped_name):
                print(f'Skipping already stripped file {filename}')
                continue
        except ValueError as e:
            print(e)

        strip(client, filepath, stripped_name)


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, client):
        super().__init__()
        self.client = client

    def process_IN_CREATE(self, event):
        print("Notified of create:", event.pathname)
        try:
            strip(self.client, event.pathname, get_stripped_name(event.pathname))
        except ValueError as e:
            print(e)


@click.command()
@click.argument('path')
@click.option('--open-ai-key', envvar='OPEN_AI_KEY', help='OpenAI API key')
@click.option('--output', help='Audio file with result')
@click.option('--load', is_flag=True, help='Load previous transcription')
@click.option('--monitor', is_flag=True, help='Monitor the given path')
def main(path, open_ai_key, output, load, monitor):
    client = OpenAI(api_key=open_ai_key)

    if monitor:
        strip_all(client, path)
        print(f'Monitoring {path}')
        manager = pyinotify.WatchManager()  # Watch Manager
        handler = EventHandler(client)
        notifier = pyinotify.Notifier(manager, handler)
        _ = manager.add_watch(
            path,
            pyinotify.IN_CREATE,
            rec=True)

        notifier.loop()
    else:
        strip(client, path, output, load)


if __name__ == "__main__":
    main()
