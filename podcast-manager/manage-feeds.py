#!/usr/bin/env python

import datetime
import hashlib
import os
from time import sleep
import sys

from feedgen.feed import FeedGenerator
import feedparser
import requests

podcast_directory = sys.argv[1] if len(sys.argv) > 1 else './'

feeds = [
    {
        'name': 'Freakonomics',
        'url': 'https://feeds.simplecast.com/Y8lFbOT4',
        'since': '2024-10-11'
    },
    # {
    #     'name': 'AstronomyCast',
    #     'url': 'https://astronomycast.libsyn.com/rss',
    #     'since': '2024-09-01'
    # },
    # {
    #     'name': '99pi',
    #     'url': 'https://feeds.99percentinvisible.org/99percentinvisible',
    # },
]


def get_filename(year, month, day, feed_name, id, stripped=False):
    return (f'{year}-{month:02}-{day:02}'
            + f'-{feed_name}'
            + f'-{hashlib.sha256(id.encode()).hexdigest()}'
            + ('-stripped' if stripped else '')
            + '.mp3')


def create_podcast_feed(parsed_input_feed):
    output = FeedGenerator()
    output.title(input.feed.title)
    output.link(href=f'https://rhew.org/podcasts/{feed["name"]}.xml',
                rel='self')
    output.description(input.feed.description)

    output.load_extension('podcast')
    output.podcast.itunes_category('Technology', 'Podcasting')

    # output.subtitle(input.feed.subtitle)
    # output.updated(input.feed.updated)
    # output.id(input.feed.id)
    return output


def download_episode(url, output_path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; PodcastDownloader/1.0; +http://rhew.org)'
    }

    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        # Save the file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        print(f"Downloaded: {output_path} from {response.url}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to download {output_path}: {e}")


def add_episode(output, input_episode, episode_url):
    output_episode = output.add_entry()
    output_episode.id(input_episode.id)
    output_episode.title(input_episode.title)
    output_episode.description(input_episode.description)
    output_episode.enclosure(episode_url, 0, 'audio/mpeg')
    output_episode.published(input_episode.published)
    output_episode.summary(input_episode.summary)


while True:
    for feed in feeds:

        input = feedparser.parse(feed['url'])
        output = create_podcast_feed(input)

        feed_directory = os.path.join(podcast_directory, feed['name'])
        os.makedirs(feed_directory, exist_ok=True)

        for input_episode in input.entries:
            published = datetime.datetime(*(input_episode['published_parsed'][0:6]))
            last_quarter = datetime.datetime.now() - datetime.timedelta(weeks=13)
            if published < last_quarter:
                continue
            if 'since' in feed and published < datetime.datetime.strptime(feed['since'], "%Y-%m-%d"):
                continue
            episode_filename = get_filename(
                input_episode['published_parsed'][0],
                input_episode['published_parsed'][1],
                input_episode['published_parsed'][2],
                feed['name'],
                input_episode.id
            )
            episode_filename_stripped = get_filename(
                input_episode['published_parsed'][0],
                input_episode['published_parsed'][1],
                input_episode['published_parsed'][2],
                feed['name'],
                input_episode.id,
                stripped=True
            )
            episode_path = os.path.join(feed_directory, episode_filename)
            episode_path_stripped = os.path.join(feed_directory, episode_filename_stripped)
            episode_url = f'https://rhew.org/podcasts/{feed["name"]}/{episode_filename}'
            episode_url_stripped = f'https://rhew.org/podcasts/{feed["name"]}/{episode_filename_stripped}'

            for link in [link
                         for link in input_episode.links
                         if link['type'] == 'audio/mpeg']:

                if os.path.isfile(episode_path_stripped):
                    add_episode(output, input_episode, episode_url_stripped)
                else:
                    if not os.path.isfile(episode_path):
                        print(f"Downloading {episode_filename}.")
                        download_episode(link['href'], episode_path)

                    add_episode(output, input_episode, episode_url)

        output.rss_file(os.path.join(podcast_directory, f'{feed["name"]}.xml'))

    print('will check back in an hour')
    sleep(3600)
