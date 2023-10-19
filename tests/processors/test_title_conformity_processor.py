import unittest
from unittest.mock import Mock
from lemmymodbot import TitleConformityProcessor, ContentResult, ContentType, Content


class TestTitleConformityProcessor(unittest.TestCase):
    def setUp(self):
        self.mock_content = Mock()
        self.mock_handle = Mock()

    def test_execute_no_comment(self):
        # Test when the content type is not POST_TITLE, no comment should be posted.
        processor = TitleConformityProcessor("your_regex_pattern", "Your message")

        result = processor.execute(Content(
            "",
            "",
            "",
            ContentType.POST_LINK
        ), self.mock_handle)

        self.mock_handle.post_comment.assert_not_called()

    def test_execute_comment(self):
        # Test when the content type is POST_TITLE and the pattern doesn't match, a comment should be posted.
        processor = TitleConformityProcessor(".* \(\(", "Your message")

        self.mock_content.type = ContentType.POST_TITLE
        self.mock_content.content = "Title that doesn't match the pattern"
        result = processor.execute(self.mock_content, self.mock_handle)

        self.mock_handle.post_comment.assert_called_with("Your message")

    def test_execute_nothing(self):
        # Test when the content type is POST_TITLE and the pattern matches, no comment should be posted.
        processor = TitleConformityProcessor(".* \(\(", "Your message")

        self.mock_content.type = ContentType.POST_TITLE
        self.mock_content.content = "Title that matches the pattern (("
        result = processor.execute(self.mock_content, self.mock_handle)

        self.mock_handle.post_comment.assert_not_called()