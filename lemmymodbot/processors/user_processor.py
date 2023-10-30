from typing import List

from lemmymodbot.processors import Processor, Content, LemmyHandle, ContentResult
from lemmymodbot.processors.base import ContentType


class UserProcessor(Processor):
    user_watch_list: List[str]

    def __init__(self, user_watch_list: List[str]):
        self.user_watch_list = user_watch_list

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        if content.type == ContentType.POST_LINK:
            return ContentResult.nothing()

        if content.actor_id in self.user_watch_list:
            return ContentResult(['user_watch_list'], None)
        return ContentResult.nothing()
