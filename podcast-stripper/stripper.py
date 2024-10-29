#!/usr/bin/env python

import datetime
import contextlib
from glob import glob
import json
import subprocess
import tempfile
import os
import pickle

import click
from openai import OpenAI, RateLimitError
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


def write_sponsor(client, company, file):
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="onyx",
        input=f"This podcast is sponsored by, {company}.",
        response_format='wav'
    ) as response:
        response.stream_to_file(file)


def write_segment(start_time, end_time, audio_file, segment_file):
    subprocess.run(['ffmpeg', '-y',
                    '-loglevel', 'error', '-hide_banner',
                    '-i', audio_file,
                    '-ss', srt_format(start_time),
                    '-t', srt_format(end_time - start_time),
                    segment_file])


def write_last_segment(time, audio_file, segment_file):
    subprocess.run(['ffmpeg', '-y',
                    '-loglevel', 'error', '-hide_banner',
                    '-i', audio_file,
                    '-sseof', srt_format(time),
                    segment_file])


def join_segments(segment_files, output_file):
    subprocess.run(['ffmpeg', '-y',
                    '-loglevel', 'error', '-hide_banner',
                    '-i', f'concat:{"|".join(segment_files)}',
                    '-c', 'copy',
                    output_file])


def write_trimmed(client, audio_file, transcript, commercial_data, output_file):
    num_segments = len(commercial_data) * 2 + 1
    with contextlib.ExitStack() as stack:
        segment_files = [stack.enter_context(tempfile.NamedTemporaryFile(suffix='.wav')) for i in range(num_segments)]

        end_commercial_index = 0
        segment_file_index = 0
        for commercial in commercial_data:
            start_time = transcript.segments[commercial['start_line']].start
            end_time = transcript.segments[commercial['end_line']].end

            if start_time < end_commercial_index:
                raise IndexError("List of commercials must be sequential.")

            print(f"{int(end_time - start_time)} second message "
                  + f"from {commercial['sponsor']} "
                  + f"at {srt_format(start_time)} to {srt_format(end_time)}.")

            write_segment(start_time, end_time, audio_file, segment_files[segment_file_index])
            segment_file_index += 1
            write_sponsor(client, commercial['sponsor'], segment_files[segment_file_index])
            segment_file_index += 1

            end_commercial_index = end_time

        write_last_segment(end_commercial_index, audio_file, segment_files[segment_file_index])
        join_segments(segment_files, output_file)


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


def get_length(filename):
    output = subprocess.check_output(
        ['ffprobe',
         '-v', 'error',
         '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1',
         filename],
        encoding='utf-8')
    return int(float(output))


def reduce_audio_file(filename):
    file_size = os.path.getsize(filename)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        fp.close()
    subprocess.run(['ffmpeg', '-i', filename, '-y',
                    '-loglevel', 'error', '-hide_banner',
                    '-c:a', 'libmp3lame',
                    '-ac', '1',      # mono
                    '-ar', '12000',  # 8k produces artifacts in audio
                    '-map', 'a',     # remove embedded cover art
                    '-vn', fp.name])
    print(f"Reduced from {file_size} to {os.path.getsize(fp.name)} before transcribing.")
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
    MAX_PODCAST_LENGTH = 60*60
    if get_length(path) > MAX_PODCAST_LENGTH:
        print(f'Skipping. {os.path.basename(path)} is longer than {MAX_PODCAST_LENGTH} seconds.')
        return
    try:
        transcript = get_transcript(client, path, load)
        commercials = get_commercials(client, transcript)
        write_trimmed(client, path, transcript, commercials, output)
    except RateLimitError as error:
        raise error


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

        try:
            strip(client, filepath, stripped_name)
        except ValueError as e:
            print(f'Failed to strip {filepath}: {e}')


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
