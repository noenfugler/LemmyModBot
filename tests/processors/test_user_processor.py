import unittest
from unittest.mock import Mock

from lemmymodbot import UserProcessor, Content, ContentType


class TestUserWatchListProcessor(unittest.TestCase):

    def test_execute_post_link(self):
        user_watch_list = UserProcessor(["user1", "user2"])
        content = Content(
            "",
            "https://example.com/some-link",
            "",
            type=ContentType.POST_LINK,
            link_to_content="https://example.com"
        )
        handle = Mock()

        result = user_watch_list.execute(content, handle)

        self.assertListEqual(result.flags, [])
        self.assertIsNone(result.extras)

    def test_execute_user_in_watch_list(self):
        user_watch_list = UserProcessor(["user1", "user2"])
        content = Content(
            "",
            "https://example.com/some-content",
            "user2",
            type=ContentType.COMMENT,
            link_to_content="https://example.com"
        )
        handle = Mock()

        result = user_watch_list.execute(content, handle)

        self.assertListEqual(result.flags, ['user_watch_list'])
        self.assertIsNone(result.extras)

    def test_execute_user_not_in_watch_list(self):
        user_watch_list = UserProcessor(["user1", "user2"])
        content = Content(
            "",
            "https://example.com/some-content",
            "user3",
            type=ContentType.COMMENT,
            link_to_content="https://example.com"
        )
        handle = Mock()

        result = user_watch_list.execute(content, handle)

        self.assertListEqual(result.flags, [])
        self.assertIsNone(result.extras)

if __name__ == '__main__':
    unittest.main()
