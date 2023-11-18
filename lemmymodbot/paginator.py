import math
from abc import abstractmethod
from enum import Enum
from typing import Any, Callable

from plemmy import LemmyHttp
from plemmy.responses import GetPostsResponse, GetCommentsResponse, GetCommunityResponse


class Paginator:

    lemmy: LemmyHttp
    community: str
    community_id: int
    task: Callable

    def __init__(self, lemmy: LemmyHttp, community_name: str, task: Callable):
        self.lemmy = lemmy
        self.community = community_name
        self.community_id = GetCommunityResponse(self.lemmy.get_community(name=self.community)).community_view.community.id
        self.task = task

    @abstractmethod
    def get_page_response(self, page: int, limit: int, sort: str):
        pass

    def paginate(self, starting_page=1, limit=10, order="Old"):
        current_page = starting_page

        while True:

            print(f"Scanning page {current_page}")

            posts = self.get_page_response(current_page, limit, order).posts

            for post in posts:
                post = post.post
                print(f"Processing {post.name} (url = {post.url})")
                self.task(post)

            if len(posts) < limit:
                break

            current_page += 1


class PostPaginator(Paginator):

    def get_page_response(self, page: int, limit: int, sort: str):
        return GetPostsResponse(
            self.lemmy.get_posts(
                community_id=self.community_id,
                page=page,
                limit=limit,
                sort=sort
            )
        )


class CommentPaginator(Paginator):

    def get_page_response(self, page: int, limit: int, sort: str):
        return GetCommentsResponse(
            self.lemmy.get_comments(
                community_id=self.community_id,
                page=page,
                limit=limit,
                sort=sort
            )
        )