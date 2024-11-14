import unittest
import datetime

from file_util import (
    get_filename,
    get_stripped_name,
    is_stripped_version,
    get_without_version_number,
    is_old
)

ENCODED_ID = '6ca13d52ca70c883e0f0bb101e425a89e8624de51db2d2392593af6a84118090'

GROUNDHOG_DAY_STRING = '2022-02-02'
GROUNDHOG_DAY = datetime.datetime.strptime(GROUNDHOG_DAY_STRING, "%Y-%m-%d")
BEFORE_GROUNDHOG_DAY = GROUNDHOG_DAY - datetime.timedelta(days=1)
AFTER_GROUNDHOG_DAY = GROUNDHOG_DAY + datetime.timedelta(days=1)


class TestFileUtil(unittest.TestCase):
    def test_is_old(self):
        filename_without_version = f'{GROUNDHOG_DAY_STRING}-name-{ENCODED_ID}.mp3'
        self.assertFalse(is_old(filename_without_version, BEFORE_GROUNDHOG_DAY))
        self.assertFalse(is_old(filename_without_version, GROUNDHOG_DAY))
        self.assertTrue(is_old(filename_without_version, AFTER_GROUNDHOG_DAY))

        filename_with_version = f'{GROUNDHOG_DAY_STRING}-name-{ENCODED_ID}.v1.2.3.mp3'
        self.assertFalse(is_old(filename_with_version, BEFORE_GROUNDHOG_DAY))
        self.assertFalse(is_old(filename_with_version, GROUNDHOG_DAY))
        self.assertTrue(is_old(filename_with_version, AFTER_GROUNDHOG_DAY))

    def test_get_without_version_number(self):
        self.assertEqual(
            get_without_version_number(f'{GROUNDHOG_DAY_STRING}-name-{ENCODED_ID}.mp3'),
            f'{GROUNDHOG_DAY_STRING}-name-{ENCODED_ID}.mp3'
        )
        self.assertEqual(
            get_without_version_number(f'{GROUNDHOG_DAY_STRING}-name-{ENCODED_ID}.v1.2.3.mp3'),
            f'{GROUNDHOG_DAY_STRING}-name-{ENCODED_ID}.mp3'
        )
        self.assertEqual(
            get_without_version_number(
                f'{GROUNDHOG_DAY_STRING}-name-{ENCODED_ID}.v1.2.3-33-abc123.mp3'),
            f'{GROUNDHOG_DAY_STRING}-name-{ENCODED_ID}.mp3'
        )

    def test_get_filename(self):
        self.assertEqual(
            get_filename(2022, 2, 2, 'name', 'abc123'),
            f'{GROUNDHOG_DAY_STRING}-name-{ENCODED_ID}.mp3'
        )

        self.assertEqual(
            get_filename(2022, 2, 2, 'name', 'abc123', stripped=True),
            f'{GROUNDHOG_DAY_STRING}-name-{ENCODED_ID}-stripped.mp3'
        )

    def test_get_stripped_name(self):
        self.assertEqual(
            get_stripped_name('v9.9', f'{GROUNDHOG_DAY_STRING}-name-{ENCODED_ID}.mp3'),
            f'{GROUNDHOG_DAY_STRING}-name-{ENCODED_ID}-stripped.v9.9.mp3'
        )

        get_stripped_name('v9.9', 'foo.mp3')

        with self.assertRaises(ValueError):
            get_stripped_name('v9.9', 'foo-stripped.mp3')

        with self.assertRaises(ValueError):
            get_stripped_name('v9.9', 'foo.baz')

    def test_is_stripped_version(self):
        self.assertTrue(is_stripped_version('foo.mp3', 'foo-stripped.mp3'))
        self.assertTrue(is_stripped_version('foo/bar/baz.mp3', 'foo/bar/baz-stripped.mp3'))
        self.assertTrue(is_stripped_version(
            'foo/bar/baz.mp3',
            'foo/bar/baz-stripped.v9.9.9.mp3')
        )
        self.assertTrue(is_stripped_version(
            'foo/bar/baz.v1.2.3.mp3',
            'foo/bar/baz-stripped.v9.9.9.mp3')
        )
