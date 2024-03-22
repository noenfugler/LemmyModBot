import unittest
from unittest.mock import Mock

from lemmymodbot import AccountAgeProcessor, LemmyHandle, Content, ContentType


class TestAccountAgeProcessor(unittest.TestCase):

    def setUp(self):
        # Mock LemmyHandle and format_duration for testing
        self.mock_handle = Mock(spec=LemmyHandle)
        self.mock_format_duration = Mock(side_effect=lambda duration, _: f"{duration}")

    def test_account_age_greater_than_minimum(self):
        # Set up the processor with a minimum age of 100
        processor = AccountAgeProcessor(100)

        # Mock account details to have an age greater than the minimum
        self.mock_handle.get_account_details.return_value.age = 150

        # Execute the processor
        result = processor.execute(self.create_mock_content(), self.mock_handle)

        # Ensure that no comments are posted and nothing is removed
        self.mock_handle.post_comment.assert_not_called()
        self.mock_handle.remove_thing.assert_not_called()

        # Ensure the result is ContentResult.nothing()
        self.assertEqual(result.flags, [])

    def test_account_age_less_than_minimum(self):
        # Set up the processor with a minimum age of 100
        processor = AccountAgeProcessor(100)

        # Mock account details to have an age less than the minimum
        self.mock_handle.get_account_details.return_value.age = 50

        result = processor.execute(self.create_mock_content(), self.mock_handle)

        # Ensure that a comment is posted and the thing is removed
        self.mock_handle.post_comment.assert_called_once_with(
            "Your account is under the minimum age required by this community (1 minutes, 40 seconds)"
        )
        self.mock_handle.remove_thing.assert_called_once_with("Account under minimum age")

        # Ensure the result is ContentResult.nothing()
        self.assertEqual(result.flags, [])

    @staticmethod
    def create_mock_content():
        # Helper method to create a mock Content object for testing
        return Content(community="test_community", content="test_content", actor_id="test_actor",
                       link_to_content="test_link", type=ContentType.COMMENT)
