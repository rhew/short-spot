import unittest

from openai_util import combine_commercial_group, combine_commercials


class TestCombineCommercials(unittest.TestCase):
    def test_combine_commercials_one(self):
        self.assertEqual(list(combine_commercials([
            {
                'sponsor': 'Some Company',
                'start_line': 77,
                'end_line': 80
            }
        ])), [
            {
                'sponsor': 'Some Company',
                'start_line': 77,
                'end_line': 80
            }
        ])

    def test_combine_commercials_two_separate(self):
        self.assertEqual(list(combine_commercials([
            {
                'sponsor': 'Some Company',
                'start_line': 77,
                'end_line': 80
            },
            {
                'sponsor': 'Some Other Company',
                'start_line': 103,
                'end_line': 111
            }
        ])), [
            {
                'sponsor': 'Some Company',
                'start_line': 77,
                'end_line': 80
            },
            {
                'sponsor': 'Some Other Company',
                'start_line': 103,
                'end_line': 111
            }
        ])

    def test_combine_commercials_two_together(self):
        self.assertEqual(list(combine_commercials([
            {
                'sponsor': 'Some Company',
                'start_line': 77,
                'end_line': 90
            },
            {
                'sponsor': 'Some Other Company',
                'start_line': 91,
                'end_line': 111
            }
        ])), [
            {
                'sponsor': 'Some Company and Some Other Company',
                'start_line': 77,
                'end_line': 111
            }
        ])

    def test_combine_commercials(self):
        self.assertEqual(list(combine_commercials([
            {
                'sponsor': 'Some Company',
                'start_line': 77,
                'end_line': 80
            },
            {
                'sponsor': 'Some Other Company',
                'start_line': 103,
                'end_line': 111
            },
            {
                'sponsor': 'Penultimate Company',
                'start_line': 113,
                'end_line': 115
            },
            {
                'sponsor': 'Still Another Company',
                'start_line': 115,
                'end_line': 120
            }
        ])), [
                {
                    'sponsor': 'Some Company',
                    'start_line': 77,
                    'end_line': 80
                },
                {
                    'sponsor': 'Some Other Company, Penultimate Company, and Still Another Company',
                    'start_line': 103,
                    'end_line': 120
                }
        ])


class TestCommercialGroups(unittest.TestCase):
    def test_combine_commercial_group_of_two(self):
        self.assertEqual(combine_commercial_group([
            {
                'sponsor': 'Some Company',
                'start_line': 77,
                'end_line': 80
            },
            {
                'sponsor': 'Some Other Company',
                'start_line': 103,
                'end_line': 111
            }
        ]),
            {
                'sponsor': 'Some Company and Some Other Company',
                'start_line': 77,
                'end_line': 111
            }
        )

    def test_combine_commercial_group_of_one(self):
        self.assertEqual(combine_commercial_group([
            {
                'sponsor': 'Some Company',
                'start_line': 77,
                'end_line': 80
            }
        ]),
            {
                'sponsor': 'Some Company',
                'start_line': 77,
                'end_line': 80
            }
        )

    def test_combine_commercial_group_of_three(self):
        self.assertEqual(combine_commercial_group([
            {
                'sponsor': 'Some Company',
                'start_line': 77,
                'end_line': 80
            },
            {
                'sponsor': 'Some Other Company',
                'start_line': 103,
                'end_line': 111
            },
            {
                'sponsor': 'Still Another Company',
                'start_line': 113,
                'end_line': 115
            }
        ]),
            {
                'sponsor': 'Some Company, Some Other Company, and Still Another Company',
                'start_line': 77,
                'end_line': 115
            }
        )
