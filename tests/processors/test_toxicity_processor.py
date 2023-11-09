import unittest
from unittest.mock import Mock
import torch
from lemmymodbot import ToxicityProcessor, ContentType, Content


class TestToxicityProcessor(unittest.TestCase):

    def test_execute_post_link(self):
        processor = ToxicityProcessor()
        content = Content(
            "",
            "https://example.com/some-link",
            "",
            type=ContentType.POST_LINK,
            link_to_content="https://example.com"
        )
        handle = Mock()

        result = processor.execute(content, handle)

        self.assertListEqual(result.flags, [])
        self.assertIsNone(result.extras)

    def test_execute_non_toxic_content(self):
        classifier = Mock()
        classifier.classify.return_value = torch.tensor([0.1, 0.9]), 0, 0
        processor = ToxicityProcessor(classifier)
        content = Content(
            "",
            "This is a non-toxic comment.",
            "",
            type=ContentType.COMMENT,
            link_to_content="https://example.com"
        )
        handle = Mock()

        result = processor.execute(content, handle)

        self.assertListEqual(result.flags, [])
        self.assertDictEqual(result.extras, {
            "toxicity": 0.1,
            "non_toxicity": 0.9,
        })

    def test_execute_potentially_toxic_content(self):
        classifier = Mock()
        classifier.classify.return_value = torch.tensor([0.2, 0.8]), 1, 0.3
        processor = ToxicityProcessor(classifier)
        content = Content(
            "",
            "This is a potentially toxic comment.",
            "",
            type=ContentType.COMMENT,
            link_to_content="https://example.com"
        )
        handle = Mock()

        result = processor.execute(content, handle)

        self.assertListEqual(result.flags, ['potentially toxic'])
        self.assertDictEqual(result.extras, {
            "toxicity": 0.2,
            "non_toxicity": 0.8,
        })


if __name__ == '__main__':
    unittest.main()
