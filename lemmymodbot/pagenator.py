import math
from abc import abstractmethod
from enum import Enum
from typing import Any, Callable

from plemmy import LemmyHttp
from plemmy.responses import GetPostsResponse, GetCommentsResponse, GetCommunityResponse

class Pagenator:

    lemmy: LemmyHttp
    community: str
    community_id: int
    task: Callable

    def __init__(self, lemmy: LemmyHttp, community_name: str):

        self.lemmy = lemmy
        self.community = community_name
        self.community_id = GetCommunityResponse(self.lemmy.get_community(name=self.community)).community_view.community.id


    @abstractmethod
    def response(self, community_id: int, page: int, limit: int, sort: str):
        pass

    def paginate(self, starting_page=1, limit=10, order="Old"):

        current_page = starting_page

        while True:

            print(f"Scanning page {current_page}")

            post_response = self.response(self.community_id, current_page, limit, order)

            posts = post_response.posts

            for post in posts:
                post = post.post
                print(f"Processing {post.name} (url = {post.url})")
                self.task(post)
                #self.process_content(post)

            if len(posts) < limit:
                break

            current_page += 1

class PostPagenator(Pagenator):

    def response(self, community_id: int, page: int, limit: int, sort: str):
        return GetPostsResponse(
            self.lemmy.get_posts(
                community_id=community_id,
                page=page,
                limit=limit,
                sort=sort
            )
        )


class CommentPagenator(Pagenator):

    def response(self, community_id: int, page: int, limit: int, sort: str):
        return GetCommentsResponse(
            self.lemmy.get_comments(
                community_id=community_id,
                page=page,
                limit=limit,
                sort=sort
            )
        )