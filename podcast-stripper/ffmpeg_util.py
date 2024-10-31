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


def seconds_to_ffmpeg_format(time_s):
    return datetime.datetime.strftime(
        datetime.datetime.utcfromtimestamp(float(time_s)), '%H:%M:%S.%f')[:-3]


def write_audio_clip(input_file, output_file, start_time_s, end_time_s=None):
    print(f'Writing from {input_file} to {output_file}; from {start_time_s} to {end_time_s}')
    if end_time_s is not None:
        command = [
            'ffmpeg',
            '-y',
            '-loglevel',
            'error',
            '-hide_banner',
            '-i',
            input_file,
            '-ss',
            seconds_to_ffmpeg_format(start_time_s),
            '-to',
            seconds_to_ffmpeg_format(end_time_s),
            output_file,
        ]
    else:
        sseof = seconds_to_ffmpeg_format(
                get_duration_s(input_file) - start_time_s)
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


def get_duration_s(filename):
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
