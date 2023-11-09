import unittest
from unittest.mock import Mock, patch

from lemmymodbot import PhashProcessor, Content, ContentType


class TestPhashProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = PhashProcessor()

    def test_execute_post_link(self):
        content = Content(
            community="",
            actor_id="",
            content="https://example.com/some-image.jpg",
            type=ContentType.POST_LINK,
            link_to_content="https://example.com"
        )
        handle = Mock()
        handle.database.url_exists.return_value = None
        handle.fetch_image.return_value = ("image_data", "phash_value")
        handle.database.phash_exists.return_value = False
        handle.database.add_phash.return_value = None

        result = self.processor.execute(content, handle)

        self.assertEqual(result.extras, {"phash": "phash_value"})
        handle.post_comment.assert_not_called()

    def test_execute_existing_phash(self):
        content = Content(
            community="",
            actor_id="",
            content="https://example.com/some-image.jpg",
            type=ContentType.POST_LINK,
            link_to_content="https://example.com"
        )
        handle = Mock()
        handle.database.url_exists.return_value = None
        handle.fetch_image.return_value = ("image_data", "phash_value")
        handle.database.phash_exists.return_value = True
        handle.database.add_phash.return_value = None
        handle.database.get_post_links_by_phash.return_value = ["test"]

        result = self.processor.execute(content, handle)

        self.assertEqual(result.extras, {"phash": "phash_value"})

    def test_execute_existing_url(self):
        content = Content(
            community="",
            actor_id="",
            content="https://example.com/some-image.jpg",
            type=ContentType.POST_LINK,
            link_to_content="https://example.com"
        )
        handle = Mock()
        handle.database.url_exists.return_value = "phash_value"
        handle.fetch_image.return_value = ("image_data", "phash_value")
        handle.database.phash_exists.return_value = False
        handle.database.add_phash.return_value = None
        handle.database.get_post_links_by_phash.return_value = ["test"]

        result = self.processor.execute(content, handle)

        self.assertEqual(result.extras, {"phash": "phash_value"})

    @patch('lemmymodbot.PhashProcessor._warn_user')
    def test_execute_warning(self, mock_warn_user):
        content = Content(
            community="",
            actor_id="",
            content="https://example.com/some-image.jpg",
            type=ContentType.POST_LINK,
            link_to_content="https://example.com"
        )
        handle = Mock()
        handle.database.url_exists.return_value = None
        handle.fetch_image.return_value = ("image_data", "phash_value")
        handle.database.phash_exists.return_value = True
        handle.database.add_phash.return_value = None
        handle.database.get_post_links_by_phash.return_value = ["test"]

        self.processor.execute(content, handle)

        mock_warn_user.assert_called_once_with(handle, "phash_value")

    def test_warn_user(self):
        handle = Mock()
        handle.database.get_post_links_by_phash.return_value = ["post1", "post2"]

        result = self.processor._warn_user(handle, "phash_value")

        self.assertEqual(result.extras, {"phash": "phash_value"})
        handle.post_comment.assert_called_once_with(
            "This post appears to be a duplicate of the following posts: [link](post1), [link](post2). "
            "This could be a false positive (beep boop I am a robot)."
        )


if __name__ == '__main__':
    unittest.main()
