import unittest

from file_util import (
    build_filename,
    get_stripped_name,
    is_stripped_filename,
    find_stripped_filename,
    get_version_number,
    get_without_version_number
)

ENCODED_ID = '6ca13d52ca70c883e0f0bb101e425a89e8624de51db2d2392593af6a84118090'


class TestFileUtil(unittest.TestCase):
    def test_get_version_number(self):
        self.assertEqual(
            get_version_number(f'2022-01-01-name-{ENCODED_ID}.v1.2.3.mp3'),
            'v1.2.3'
        )
        self.assertIsNone(
            get_version_number(f'2022-01-01-name-{ENCODED_ID}.mp3')
        )

    def test_get_without_version_number(self):
        self.assertEqual(
            get_without_version_number(f'2022-01-01-name-{ENCODED_ID}.mp3'),
            f'2022-01-01-name-{ENCODED_ID}.mp3'
        )
        get_without_version_number(f'2022-01-01-name-{ENCODED_ID}.v1.2.3-33-abc123.mp3')
        self.assertEqual(
            get_without_version_number(f'2022-01-01-name-{ENCODED_ID}.v1.2.3-33-abc123.mp3'),
            f'2022-01-01-name-{ENCODED_ID}.mp3'
        )
        self.assertEqual(
            get_without_version_number(f'2022-01-01-name-{ENCODED_ID}.v1.2.3.mp3'),
            f'2022-01-01-name-{ENCODED_ID}.mp3'
        )

    def test_build_filename(self):
        self.assertEqual(
            build_filename(2022, 1, 1, 'name', 'abc123'),
            f'2022-01-01-name-{ENCODED_ID}.mp3'
        )

        self.assertEqual(
            build_filename(2022, 1, 1, 'name', 'abc123', stripped=True),
            f'2022-01-01-name-{ENCODED_ID}-stripped.mp3'
        )

    def test_get_stripped_name(self):
        self.assertEqual(
            get_stripped_name('v9.9', f'2022-01-01-name-{ENCODED_ID}.mp3'),
            f'2022-01-01-name-{ENCODED_ID}-stripped.v9.9.mp3'
        )

        get_stripped_name('v9.9', 'foo.mp3')

        with self.assertRaises(ValueError):
            get_stripped_name('v9.9', 'foo-stripped.mp3')

        with self.assertRaises(ValueError):
            get_stripped_name('v9.9', 'foo.baz')

    def test_is_stripped_filename(self):
        self.assertTrue(is_stripped_filename('foo.mp3', 'foo-stripped.mp3'))
        self.assertTrue(is_stripped_filename('foo/bar/baz.mp3', 'foo/bar/baz-stripped.mp3'))

    def test_find_stripped_filename(self):
        self.assertEqual(
            find_stripped_filename(
                '2022-01-01-name.mp3',
                ['2022-01-01-name-stripped.mp3']
            ),
            '2022-01-01-name-stripped.mp3'
        )

        self.assertEqual(
            find_stripped_filename(
                '2022-01-01-name.mp3',
                ['2022-01-01-name-stripped.mp3', '2022-01-01-name.mp3']
            ),
            '2022-01-01-name-stripped.mp3'
        )

        self.assertEqual(
            find_stripped_filename(
                '2022-01-01-name.mp3',
                ['2022-01-01-name-stripped.v1.2.3.mp3', '2022-01-01-name.mp3']
            ),
            '2022-01-01-name-stripped.v1.2.3.mp3'
        )

        self.assertIsNone(
            find_stripped_filename(
                '2022-01-01-name-abc123.mp3',
                ['2022-01-01-name.mp3']
            )
        )
