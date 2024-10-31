from difflib import SequenceMatcher
import os
from string import punctuation
import unittest

from openai import OpenAI

from openai_util import get_transcript, get_commercials

PIZZA_POD = os.path.join(os.path.dirname(__file__), 'pizza_pod.mp3')

PIZZA1_TEXT = """Welcome to Pizza Talk! I’m Pepe Roni, here to bring you a slice of delicious pizza facts in just 30 seconds! Today, let’s talk toppings. Did you know pepperoni is by far the most popular topping in the U.S.? But around the world, people are putting all kinds of things on their pizza. In Japan, you’ll find squid, in Sweden, banana curry, and in Brazil? They top it with green peas!"""  # noqa: E501

PIZZA2_TEXT = """But here’s something really surprising: pizza isn’t just about toppings—it’s all about the crust! Thin, thick, or stuffed, it’s the base of every great pizza experience. So next time you’re grabbing a slice, don’t just look at what’s on top. Give a little love to that crispy, chewy crust! Thanks for tuning in to Pizza Talk! Now, go enjoy a slice!"""  # noqa: E501

COMMERCIAL_TEXT = """At Cyberdyne Systems, we're building the future today. From advanced robotics to artificial intelligence, our cutting-edge technology enhances industries and empowers humanity. Cyberdyne Systems: Innovation, Precision, Progress. Redefining tomorrow. one breakthrough at a time."""  # noqa: E501


def just_words(original):
    return original.translate(str.maketrans("", "", punctuation)).lower().strip()


class TestOpenAIUtil(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))

    def test_just_words(self):
        self.assertEqual(just_words('hello'), 'hello')
        self.assertEqual(just_words('Hello, World!'), 'hello world')

    def test_get_transcript_and_commercials(self):
        transcript = get_transcript(self.client, PIZZA_POD)
        self.assertIsNotNone(transcript)
        self.assertGreater(
            SequenceMatcher(
                a=just_words(transcript.text),
                b=just_words(' '.join([PIZZA1_TEXT, COMMERCIAL_TEXT, PIZZA2_TEXT]))
            ).ratio(),
            0.9
        )

        commercials = get_commercials(self.client, transcript)
        self.assertGreater(
            SequenceMatcher(
                a=just_words(commercials[0]['sponsor']),
                b=just_words('Cyberdyne Systems')
            ).ratio(),
            0.9
        )

        found_commercial_text = ' '.join([
            transcript.segments[segment_index].text
            for segment_index in range(
                commercials[0]['start_line'],
                commercials[0]['end_line'] + 1
            )])
        self.assertGreater(
            SequenceMatcher(
                a=just_words(found_commercial_text),
                b=just_words(COMMERCIAL_TEXT)
            ).ratio(),
            0.9
        )
