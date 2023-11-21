from abc import abstractmethod

from typing import Callable

from plemmy import LemmyHttp
from plemmy.responses import GetPostsResponse, GetCommentsResponse, GetCommunityResponse

from lemmymodbot.data import MonitorPersistence, PostMonitorPersistence, CommentMonitorPersistence


class Paginator:
    lemmy: LemmyHttp
    persistence: MonitorPersistence
    community: str
    community_id: int

    def __init__(self, lemmy: LemmyHttp, community_name: str):
        self.lemmy = lemmy
        self.community = community_name
        self.community_id = GetCommunityResponse(
            self.lemmy.get_community(name=self.community)).community_view.community.id

        # print(self.lemmy.get_community(name=self.community).json())

    @abstractmethod
    def get_page_response(self, page: int, limit: int, sort: str):
        pass

    def paginate(self, task: Callable, starting_page: int = None, limit: int = 10):
        current_page = starting_page if starting_page is not None else self.persistence.get_current_page(self.community)

        while True:

            print(f"Scanning page {current_page}")

            content_list = self.get_page_response(current_page, limit, "Old")

            for content in content_list:
                post_v = content.post
                print(f"Processing {post_v.name} (url = {post_v.url})")
                task(content)

            if len(content_list) < limit:
                break

            current_page += 1

        self.persistence.set_current_page(self.community, current_page)


class PostPaginator(Paginator):

    def __init__(self, lemmy: LemmyHttp, community_name: str,
                 monitor_persistence: MonitorPersistence = PostMonitorPersistence()):
        super().__init__(lemmy, community_name)
        self.persistence = monitor_persistence

    def get_page_response(self, page: int, limit: int, sort: str):
        posts = self.lemmy.get_posts(
            community_id=self.community_id,
            page=page,
            limit=limit,
            sort=sort
        )

        return GetPostsResponse(
            posts
        ).posts


class CommentPaginator(Paginator):

    def __init__(self, lemmy: LemmyHttp, community_name: str,
                 monitor_persistence: MonitorPersistence = CommentMonitorPersistence()):
        super().__init__(lemmy, community_name)
        self.persistence = monitor_persistence

    def get_page_response(self, page: int, limit: int, sort: str):
        return GetCommentsResponse(
            self.lemmy.get_comments(
                community_id=self.community_id,
                page=page,
                limit=limit,
                sort=sort
            )
        ).comments
