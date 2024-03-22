import unittest
from unittest.mock import Mock, patch
from lemmymodbot.processors import Content
from lemmymodbot.processors.spam_image_processor import SpamImageProcessor, ContentType


class TestSpamImageProcessor(unittest.TestCase):
    @patch('lemmymodbot.processors.spam_image_processor.extract_links_from_markdown')
    def test_execute_post_link(self, mock_extract_links):
        mock_handle = Mock()
        mock_handle.fetch_image.return_value = (None, "dummy_hash")

        mock_extract_links.return_value = []
        processor = SpamImageProcessor(["dummy_hash"])
        content = Content("", "http://example.com/image.jpg", "", "", ContentType.POST_LINK)
        result = processor.execute(content, mock_handle)

        mock_handle.remove_thing.assert_called_once_with("Spam image detected")
        self.assertEqual(result.flags, [])

    @patch('lemmymodbot.processors.spam_image_processor.extract_links_from_markdown')
    def test_execute_post_body(self, mock_extract_links):
        mock_handle = Mock()
        mock_handle.fetch_image.return_value = (None, "dummy_hash")

        mock_extract_links.return_value = ["http://example.com/image.jpg"]
        processor = SpamImageProcessor(["dummy_hash"])
        content = Content("", "Here is an image: ![alt text](http://example.com/image.jpg)", "", "", ContentType.POST_BODY)
        result = processor.execute(content, mock_handle)

        mock_handle.remove_thing.assert_called_once_with("Spam image detected")
        self.assertEqual(result.flags, [])

    @patch('lemmymodbot.processors.spam_image_processor.extract_links_from_markdown')
    def test_execute_comment(self, mock_extract_links):
        mock_handle = Mock()
        mock_handle.fetch_image.return_value = (None, "dummy_hash")

        mock_extract_links.return_value = ["http://example.com/image.jpg"]
        processor = SpamImageProcessor(["dummy_hash"])
        content = Content("", "Here is an image: ![alt text](http://example.com/image.jpg)", "", "", ContentType.COMMENT)
        result = processor.execute(content, mock_handle)

        mock_handle.remove_thing.assert_called_once_with("Spam image detected")
        self.assertEqual(result.flags, [])

    def test_execute_no_spam_image(self):
        mock_handle = Mock()
        mock_handle.fetch_image.return_value = (None,None)

        processor = SpamImageProcessor(["dummy_hash"])
        content = Content("", "http://example.com/not_an_image", "", "", ContentType.POST_LINK)
        result = processor.execute(content, mock_handle)

        mock_handle.remove_thing.assert_not_called()
        self.assertEqual(result.flags, [])


if __name__ == '__main__':
    unittest.main()
