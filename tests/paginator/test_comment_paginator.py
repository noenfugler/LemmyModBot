import unittest
from unittest.mock import Mock

import requests


class TestCommentPaginator(unittest.TestCase):
    def setUp(self):
        self.mock_lemmy = Mock()
        self.mock_handle = Mock()

        with open('tests/fixtures/community_response_ok.json') as f:
            # self.mock_community_response = f.read()

            response = requests.Response()
            response._content = f.read()
            self.mock_lemmy.get_community.return_value = response

    def test_get_page_response_called_correct_number_of_times(self):
        pass

    def test_correct_final_current_page(self):
        pass

    def test_task_called_correct_number_of_times(self):
        pass
