#!/usr/bin/env python

import datetime
import os
import subprocess


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


def join_segments_mp3(input_file_list, output_file, video_file=None):
    print(f'Joining {input_file_list} to {output_file}')
    command = [
        'ffmpeg',
        '-y',
        '-loglevel',
        'error',
        '-hide_banner',
        '-i',
        f'concat:{"|".join(input_file_list)}',
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
