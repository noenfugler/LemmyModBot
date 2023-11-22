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

    def test_task_called_correct_number_of_times(self):

        mock_persistence = Mock()
        mock_persistence.get_current_page.return_value = 1
        mock_persistence.set_current_page.method()

        post_paginator = PostPaginator(
            lemmy=self.mock_lemmy,
            community_name="196",
            monitor_persistence=mock_persistence
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
        mock_persistence = Mock()
        mock_persistence.get_current_page.return_value = 1
        mock_persistence.set_current_page.method()

        post_paginator = PostPaginator(
            lemmy=self.mock_lemmy,
            community_name="196",
            monitor_persistence=mock_persistence
        )

        post_ten = json.loads(Path('tests/fixtures/get_posts_response_ok.json').read_text())
        post_empty = json.loads(Path('tests/fixtures/get_posts_response_empty.json').read_text())

        response = Mock()
        response.json.side_effect = [post_ten, post_empty]

        self.mock_lemmy.get_posts.return_value = response

        mock_task = Mock()
        mock_task.method()

        post_paginator.paginate(mock_task, 1, 10)

        self.mock_lemmy.get_posts.assert_called_with(
            community_id=70513,
            page=2,
            limit=10,
            sort="Old"
        )

