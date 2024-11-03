import os
import unittest

from playlist import Playlist


class TestPlaylist(unittest.TestCase):
    def test_empty_playlist(self):
        playlist = Playlist()
        self.assertEqual(0, len(playlist.get_files()))

    def test_new_file(self):
        playlist = Playlist()
        playlist.new_file()
        self.assertEqual(1, len(playlist.get_files()))
        self.assertTrue(os.path.isfile(playlist.get_files()[0]))

    def test_default_suffix(self):
        playlist = Playlist()
        playlist.new_file()
        self.assertTrue(playlist.get_files()[0].endswith('.mp3'))

    def test_suffix(self):
        playlist = Playlist()
        playlist.new_file(suffix='.mp4')
        self.assertTrue(playlist.get_files()[0].endswith('.mp4'))

    def test_playlist_with_three(self):
        playlist = Playlist()
        playlist.new_file()
        playlist.new_file()
        playlist.new_file()
        self.assertEqual(3, len(playlist.get_files()))
