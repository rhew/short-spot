#!/usr/bin/env python

import datetime
import os
import subprocess
import tempfile


# This function writes a new audio file with the data essential for
# understanding speech.
def reduce_audio_file(input_file, output_file):
    command = [
        'ffmpeg',
        '-y',
        '-loglevel',
        'error',
        '-hide_banner',
        '-i',
        input_file,
        '-vn',
        '-ac',
        '1',
        '-ar',
        '12000',
        output_file,
    ]
    subprocess.run(command)


def seconds_to_ffmpeg_format(time):
    return datetime.datetime.strftime(
        datetime.datetime.utcfromtimestamp(float(time)), '%H:%M:%S.%f')[:-3]


def write_audio_clip(input_file, output_file, start_time, end_time=None):
    if end_time is not None:
        print(f'Writing from {input_file} to {output_file}; from {start_time} to {end_time}')
        command = [
            'ffmpeg',
            '-y',
            '-loglevel',
            'error',
            '-hide_banner',
            '-i',
            input_file,
            '-ss',
            seconds_to_ffmpeg_format(start_time),
            '-to',
            seconds_to_ffmpeg_format(end_time),
            output_file,
        ]
    else:
        sseof = seconds_to_ffmpeg_format(
                get_duration(input_file) - start_time)
        print(f'Writing the last {sseof} seconds of {input_file} to {output_file}')
        command = [
            'ffmpeg',
            '-y',
            '-loglevel',
            'error',
            '-hide_banner',
            '-sseof',
            f'-{sseof}',
            '-i',
            input_file,
            output_file,
        ]
    subprocess.run(command)


def join_segments_mp3(input_file_list, output_file):
    print(f'Joining {input_file_list} to {output_file}')
    command = [
        'ffmpeg',
        '-y',
        '-loglevel',
        'error',
        '-hide_banner',

        # Input [0]: one second of silence
        '-f',
        'lavfi',
        '-t',
        '1',
        '-i',
        'anullsrc=r=22000:cl=mono',

        # input [1]-[n], one for each file
    ] + list(sum([('-i', file) for file in input_file_list], ())) + [

        # Describe the concatenation
        '-filter_complex',
        '[0]'.join([f'[{n+1}]' for n in range(len(input_file_list))]) +
        f'concat=n={str(2*len(input_file_list)-1)}:v=0:a=1',

        '-c:a',
        'libmp3lame',
        output_file
    ]
    print(f'Command: {command}')
    subprocess.run(command)


def get_size(filename):
    return os.path.getsize(filename)


def get_duration(filename):
    command = [
        'ffprobe',
        '-v',
        'error',
        '-show_entries',
        'format=duration',
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        filename,
    ]
    return float(subprocess.check_output(command, encoding='utf-8'))


def add_image(podcast, image_file):
    if image_file is None:
        return
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_podcast:
        command = [
            'ffmpeg',
            '-y',
            '-loglevel',
            'error',
            '-hide_banner',
            '-i',
            podcast,
            '-i',
            image_file,
            '-map',
            '0:0',
            '-map',
            '1:0',
            '-c:v',
            'copy',
            temp_podcast.name
        ]
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as error:
            print(f'Failed to add image {image_file} to {podcast}: {error}')
            print(' '.join(command))
        subprocess.run(['cp', temp_podcast.name, podcast])


def get_image(filename):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as image_file:
        image_file.close()
        command = [
            'ffmpeg',
            '-y',
            '-loglevel',
            'error',
            '-hide_banner',
            '-i',
            filename,
            '-an',
            '-vcodec',
            'copy',
            image_file.name
        ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        print(f'Failed to extract image from {filename}')
        return None
    print(f'Extracted image from {filename}')
    return image_file.name
