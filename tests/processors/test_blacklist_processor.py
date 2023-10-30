import unittest
from unittest.mock import Mock

from lemmymodbot import BlacklistProcessor, ContentType


class TestBlacklistProcessor(unittest.TestCase):
    def setUp(self):
        self.mock_content = Mock()
        self.mock_handle = Mock()

    def test_execute_nothing_post_link(self):
        # Test when the content type is POST_LINK, the processor should return nothing.
        processor = BlacklistProcessor(["bad_word1", "bad_word2"])
        processor.setup()

        self.mock_content.type = ContentType.POST_LINK
        result = processor.execute(self.mock_content, self.mock_handle)

        self.assertEqual(result.flags, [])

    def test_execute_no_blacklist_words(self):
        # Test when the content doesn't contain any blacklist words, the processor should return nothing.
        processor = BlacklistProcessor(["bad_word1", "bad_word2"])
        processor.setup()

        self.mock_content.type = ContentType.POST_TITLE  # Assuming ContentType.OTHER_TYPE is not POST_LINK
        self.mock_content.content = "This is a normal content without bad words"
        result = processor.execute(self.mock_content, self.mock_handle)

        self.assertEqual(result.flags, [])

    def test_execute_with_blacklist_words(self):
        # Test when the content contains blacklist words, the processor should return ContentResult with a blacklist tag.
        processor = BlacklistProcessor(["bad_word1", "bad_word2"])
        processor.setup()

        self.mock_content.type = ContentType.POST_TITLE  # Assuming ContentType.OTHER_TYPE is not POST_LINK
        self.mock_content.content = "This contains bad_word1, which is on the blacklist"
        result = processor.execute(self.mock_content, self.mock_handle)

        self.assertEqual(result.flags, ['word_blacklist'])
        self.mock_handle.post_comment.assert_not_called()
