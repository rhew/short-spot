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


def timestamp_to_ffmpeg_format(timestamp):
    return datetime.datetime.strftime(
        datetime.datetime.utcfromtimestamp(timestamp), '%H:%M:%S.%f')[:-3]


def write_audio_clip(input_file, output_file, start_time, end_time=None):
    if end_time is not None:
        command = [
            'ffmpeg',
            '-y',
            '-loglevel',
            'error',
            '-hide_banner',
            '-i',
            input_file,
            '-ss',
            timestamp_to_ffmpeg_format(start_time),
            '-to',
            timestamp_to_ffmpeg_format(end_time),
            output_file,
        ]
    else:
        sseof = timestamp_to_ffmpeg_format(
                get_duration(input_file) - start_time)
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


def join_segments(input_file_list, output_file, video_file=None):
    command = [
        'ffmpeg',
        '-y',
        '-loglevel',
        'error',
        '-hide_banner',
        '-i',
        f'concat:{"|".join(input_file_list)}',
        '-c',
        'copy',
        output_file
    ]
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
