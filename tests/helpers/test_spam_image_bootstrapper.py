import unittest
from unittest.mock import Mock
from lemmymodbot.helpers import SpamImageBootstrapper
from lemmymodbot.database import Database


class TestSpamImageBootstrapper(unittest.TestCase):
    def setUp(self):
        self.database = Mock(spec=Database)
        self.bootstrapper = SpamImageBootstrapper(self.database, lambda x: (None, None))

    def test_setup_with_urls(self):
        images = ["http://example.com/image1.jpg", "http://example.com/image2.jpg"]
        self.bootstrapper.fetch_image = lambda x: (None, "phash1")
        self.database.url_exists.side_effect = [None, "existing_phash"]
        self.database.phash_exists.side_effect = [False, True]

        self.bootstrapper.setup(images)

        self.database.add_phash.assert_called_once_with("http://example.com/image1.jpg", "phash1", True)

    def test_setup_with_local_images(self):
        images = ["869f29d86362d32b"]
        self.database.phash_exists.return_value = False

        self.bootstrapper.setup(images)

        self.database.add_phash.assert_called_once_with("", "869f29d86362d32b", True)

    def test_setup_with_existing_image(self):
        images = ["http://example.com/existing_image.jpg"]
        self.bootstrapper.fetch_image = lambda x: (None, "existing_phash")
        self.database.url_exists.return_value = "existing_phash"
        self.database.phash_exists.return_value = True

        self.bootstrapper.setup(images)

        self.database.add_phash.assert_not_called()


if __name__ == '__main__':
    unittest.main()
