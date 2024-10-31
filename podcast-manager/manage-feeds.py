#!/usr/bin/env python

import datetime
import hashlib
import os
from time import sleep

import click
from feedgen.feed import FeedGenerator
import feedparser
import requests

from config import feeds


def get_filename(year, month, day, feed_name, id, stripped=False):
    return (f'{year}-{month:02}-{day:02}'
            + f'-{feed_name}'
            + f'-{hashlib.sha256(id.encode()).hexdigest()}'
            + ('-stripped' if stripped else '')
            + '.mp3')


def create_podcast_feed(parsed_input_feed, podcast_name):
    output = FeedGenerator()
    output.title(parsed_input_feed.feed.title)
    output.link(href=f'https://rhew.org/podcasts/{podcast_name}.xml',
                rel='self')
    output.description(parsed_input_feed.feed.description)

    output.load_extension('podcast')
    output.podcast.itunes_category('Technology', 'Podcasting')

    # output.subtitle(parsed_input_feed.feed.subtitle)
    # output.updated(parsed_input_feed.feed.updated)
    # output.id(parsed_input_feed.feed.id)
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


def generate_index(links):
    index_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Feeds</title>
    </head>
    <body>
        <h1>Feeds</h1>
        <ul>
    """
    # Add each link to the list
    for episode_name, url in links:
        index_html += f'<li><a href="{url}" target="_blank">{episode_name}</a></li>\n'

    # Close the HTML tags
    index_html += """
        </ul>
    </body>
    </html>
    """

    return index_html


def has_stripped_version(filename, path):
    if filename.endswith('-stripped.mp3'):
        return False
    if not os.path.isfile(os.path.join(path, filename[:-4] + '-stripped.mp3')):
        return False

    return True


def is_old(filename, since):
    published_str = '-'.join(filename.split('-')[:3])
    try:
        published = datetime.datetime.strptime(published_str, "%Y-%m-%d")
    except ValueError:
        return False

    if published >= since:
        return False

    return True


def purge_podcast_files(path):
    for feed in feeds:
        feed_directory = os.path.join(path, feed['name'])
        if not os.path.exists(feed_directory):
            continue

        since = datetime.datetime.strptime(feed['since'], "%Y-%m-%d")

        for filename in os.listdir(feed_directory):
            if not filename.endswith('.mp3'):
                continue
            if has_stripped_version(filename, feed_directory):
                print(f'Deleting {filename} with stripped version.')
                os.remove(os.path.join(feed_directory, filename))
            if is_old(filename, since):
                print(f'Deleting old {filename}.')
                os.remove(os.path.join(feed_directory, filename))


@click.command()
@click.argument('path', default='./podcasts/')
@click.option('--interval', envvar='INTERVAL', default='0',
              help='Manager will run again after this time.')
@click.option('--download/--no-download', is_flag=True, envvar='DOWNLOAD', default=True,
              help='Actually download episodes.')
def main(path, interval, download):
    while True:
        purge_podcast_files(path)
        index_html_links = []
        for feed in feeds:

            input = feedparser.parse(feed['url'])
            output = create_podcast_feed(input, feed['name'])

            feed_directory = os.path.join(path, feed['name'])
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
                            if download:
                                download_episode(link['href'], episode_path)

                        add_episode(output, input_episode, episode_url)

            output.rss_file(os.path.join(path, f'{feed["name"]}.xml'))
            index_html_links.append(
                (feed['name'],
                 f'https://rhew.org/podcasts/{feed["name"]}.xml'))

        with open(os.path.join(path, "index.html"), "w") as index_html:
            index_html.write(generate_index(index_html_links))

        if interval != '0':
            print(f'will check back in {interval} seconds')
            sleep(int(interval))
        else:
            break


if __name__ == "__main__":
    main()
