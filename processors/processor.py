from typing import List, Any, Optional, Union
import torchtext
from pylemmy import Lemmy
from pylemmy.models.comment import Comment
from pylemmy.models.post import Post
import re
from api import LemmyModHttp


class LemmyHandle:

    def __init__(self, lemmy: Lemmy, elem: Union[Post, Comment]):
        self.elem = elem
        self.lemmy = lemmy
        self.lemmy_http = LemmyModHttp(lemmy)

    def send_message_to_author(self, content: str):
        actor_id = self.elem.post_view.post.creator_id if isinstance(self.elem, Post) else self.elem.comment_view
        self.lemmy_http.send_message(actor_id, f"{content}\n\nMod bot (with L plates)")

    def post_comment(self, content: str) -> Comment:
        return self.elem.create_comment(f"{content}\n\nMod bot (with L plates)")

    def remove_thing(self, reason: str):
        if isinstance(self.elem, Post):
            self.lemmy_http.remove_post(self.elem.post_view.post.id, reason)
        elif isinstance(self.elem, Comment):
            self.lemmy_http.remove_comment(self.elem.comment_view.comment.id, reason)


class ContentType:
    POST_TITLE = 0
    POST_BODY = 1
    POST_LINK = 2
    COMMENT = 3


class Content:
    community: str
    content: str
    actor_id: str
    type: ContentType

    def __init__(self, community: str, content: str, actor_id: str, type: ContentType):
        self.community = community
        self.content = content
        self.actor_id = actor_id
        self.type = type


class ContentResult:
    flags: List[str]
    extras: Optional[Any]

    def __init__(self, flags: List[str], extras: Optional[Any]):
        self.flags = flags
        self.extras = extras

    @staticmethod
    def nothing():
        return ContentResult([], None)


class Processor:

    def setup(self) -> None:
        pass

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        return ContentResult.nothing()



