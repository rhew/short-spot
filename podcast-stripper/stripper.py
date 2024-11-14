#!/usr/bin/env python

from glob import glob
import subprocess
import tempfile
import time
import os

import click
from openai import OpenAI, RateLimitError
import pyinotify

try:
    from ..common import get_stripped_name, find_stripped_filename, is_stripped_filename
except ImportError:
    from file_util import get_stripped_name, find_stripped_filename, is_stripped_filename

from ffmpeg_util import (
    seconds_to_ffmpeg_format,
    reduce_audio_file,
    write_audio_clip,
    join_segments_mp3,
    get_duration,
    get_image,
    add_image,
)
from openai_util import (
    get_transcript,
    get_commercials,
    combine_commercials,
    write_sponsor
)

from playlist import Playlist

with open('version') as version_file:
    VERSION = version_file.read()


def get_watermarked(image_file):
    if image_file is None:
        return None

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as watermarked:
        command = [
            'convert',
            image_file,
            '(',
            'checkmark.png',
            '-resize',
            '30%x30%',
            ')',
            '-gravity',
            'northeast',
            '-geometry',
            '+5%+5%',
            '-composite',
            watermarked.name
        ]
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as error:
            print(f'Failed to watermark {image_file}: {error}')
            return image_file

        return watermarked.name


def dump_commercial(commercial):
    print(f'About this commercial from {commercial["sponsor"]}...')
    print(f'Commercial: {commercial}.')
    print(f'Start line: {commercial["start_line"]}.')
    print(f'End line: {commercial["end_line"]}.')


def dump_transcript_at_commercial(transcript, commercial):
    print(f'About the transcript for this commercial from {commercial["sponsor"]}...')
    print(f'Number of segments: {len(transcript.segments)}.')
    print(f'Segment start line: {transcript.segments[commercial["start_line"]]}.')
    print(f'Segment end line: {transcript.segments[commercial["end_line"]]}.')
    print(f'Segment start: {transcript.segments[commercial["start_line"]].start}.')
    print(f'Segment end: {transcript.segments[commercial["end_line"]].end}.')


def write_trimmed(client, audio_file, transcript, commercial_data, output_file):
    playlist = Playlist()
    image_file = get_watermarked(get_image(audio_file))
    prev_commercial_end = 0
    for commercial in commercial_data:
        try:
            commercial_start = transcript.segments[commercial['start_line']].start
            commercial_end = transcript.segments[commercial['end_line']].end
        except IndexError:
            print('Oh snap, IndexError. Let''s sneak up on it.')
            dump_commercial(commercial)
            dump_transcript_at_commercial(transcript, commercial)
            raise

        if commercial_start < prev_commercial_end:
            print('Oh snap, start before end!. Let''s sneak up on it.')
            dump_commercial(commercial)
            dump_transcript_at_commercial(transcript, commercial)
            raise IndexError("List of commercials must be sequential.")

        print(f"{int(commercial_end - commercial_start)} second message "
              + f"from {commercial['sponsor']} "
              + f"at {seconds_to_ffmpeg_format(commercial_start)} "
              + f"to {seconds_to_ffmpeg_format(commercial_end)}.")

        if commercial_start > prev_commercial_end:
            write_audio_clip(
                audio_file,
                playlist.new_file('.wav'),
                prev_commercial_end,
                commercial_start
            )
        write_sponsor(client, commercial['sponsor'], playlist.new_file('.wav'))
        prev_commercial_end = commercial_end

    write_audio_clip(
        audio_file,
        playlist.new_file('.wav'),
        prev_commercial_end
    )
    join_segments_mp3(playlist.get_files(), output_file)
    add_image(output_file, image_file)

    print(f'Reduced by {get_duration(audio_file) - get_duration(output_file)} seconds.')
    time.sleep(600)


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
        commercials = combine_commercials(get_commercials(client, transcript))
        write_trimmed(client, path, transcript, commercials, output)
    except RateLimitError as error:
        raise error


def strip_all(client, scan_directory):
    print(f'Stripping everything under {scan_directory}/*')
    for relative_path in glob(os.path.join(scan_directory, '*', '*.mp3')):
        path = os.path.join(scan_directory, relative_path)
        directory = os.path.dirname(path)
        filename = os.path.basename(path)

        if is_stripped_filename(filename):
            print(f'ignoring {filename}')
            continue

        try:
            if find_stripped_filename(filename, os.listdir(directory)):
                print(f'Skipping already stripped file {filename}')
                continue
        except ValueError as e:
            print(e)

        try:
            strip(
                client,
                path,
                os.path.join(
                    directory,
                    get_stripped_name(VERSION, filename)
                )
            )
        except ValueError as e:
            print(f'Failed to strip {filename}: {e}')


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, client):
        super().__init__()
        self.client = client

    def process_IN_CREATE(self, event):
        print("Notified of create:", event.pathname)
        if event.pathname.endswith('-stripped.mp3'):
            print(f'ignoring {event.pathname}')
            return
        try:
            strip(
                self.client,
                event.pathname,
                os.path.join(
                    os.path.dirname(event.pathname),
                    get_stripped_name(VERSION, os.path.basename(event.pathname))
                )
            )
        except ValueError as e:
            print(e)


@click.command()
@click.argument('path')
@click.option('--open-ai-key', envvar='OPEN_AI_KEY', help='OpenAI API key')
@click.option('--output', help='Audio file with result')
@click.option('--monitor', is_flag=True, help='Monitor the given path')
def main(path, open_ai_key, output, monitor):
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
