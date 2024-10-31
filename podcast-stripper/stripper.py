#!/usr/bin/env python

import datetime
import contextlib
from glob import glob
import tempfile
import os

import click
from openai import OpenAI, RateLimitError
import pyinotify


from ffmpeg_util import (
    reduce_audio_file,
    write_audio_clip,
    join_segments,
    get_duration
)
from openai_util import (
    get_transcript,
    get_commercials,
    write_sponsor
)


def srt_format(timestamp):
    return datetime.datetime.strftime(
        datetime.datetime.fromtimestamp(timestamp), "%H:%M:%S,%f")[:-3]


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

            write_audio_clip(start_time, end_time, audio_file, segment_files[segment_file_index].name)
            segment_file_index += 1
            write_sponsor(client, commercial['sponsor'], segment_files[segment_file_index].name)
            segment_file_index += 1

            end_commercial_index = end_time

        write_audio_clip(end_commercial_index, audio_file,
                         segment_files[segment_file_index].name)
        join_segments([fp.name for fp in segment_files], output_file)


def strip(client, path, output):
    print(f'Starting {os.path.basename(path)} -> {os.path.basename(output)}')
    MAX_PODCAST_LENGTH = 60*60
    if get_duration(path) > MAX_PODCAST_LENGTH:
        print(f'Skipping. {os.path.basename(path)} is longer than {MAX_PODCAST_LENGTH} seconds.')
        return
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            reduce_audio_file(path, fp.name)
            transcript = get_transcript(client, fp.name)
            fp.close()
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
        strip(client, path, output)


if __name__ == "__main__":
    main()
