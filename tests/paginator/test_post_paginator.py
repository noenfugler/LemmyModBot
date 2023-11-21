import json
import unittest
from pathlib import Path
from unittest.mock import Mock

from lemmymodbot.paginator import PostPaginator


class TestPostPaginator(unittest.TestCase):
    def setUp(self):
        self.mock_lemmy = Mock()
        self.mock_handle = Mock()

        with open('tests/fixtures/community_response_ok.json', 'r') as f:
            response = Mock()
            response.json.return_value = json.loads(f.read())
            self.mock_lemmy.get_community.return_value = response

    def test_get_page_response_called_correct_number_of_times(self):
        post_paginator = PostPaginator(
            lemmy=self.mock_lemmy,
            community_name="196"
        )

        post_ten = json.loads(Path('tests/fixtures/get_posts_response_ok.json').read_text())
        post_empty = json.loads(Path('tests/fixtures/get_posts_response_empty.json').read_text())

        response = Mock()
        response.json.side_effect = [post_ten, post_empty]

        self.mock_lemmy.get_posts.return_value = response

        mock_task = Mock()
        mock_task.method()

        post_paginator.paginate(mock_task, 1, 10)

        assert mock_task.call_count == 10

    def test_correct_final_current_page(self):
        pass

    def test_task_called_correct_number_of_times(self):
        pass
