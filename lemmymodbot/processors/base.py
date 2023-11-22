from io import BytesIO
from typing import List, Any, Optional, Union, Dict

from plemmy import LemmyHttp
from plemmy.views import PostView, CommentView


from lemmymodbot.database import Database

import requests
from PIL import Image, UnidentifiedImageError
import imagehash


class LemmyHandle:

    def __init__(self, lemmy: LemmyHttp, elem: Union[PostView, CommentView], database: Database, config, matrix_facade):
        self.elem = elem
        self.lemmy = lemmy
        self.lemmy_http = lemmy
        self.database = database
        self.config = config
        self.matrix_facade = matrix_facade

    def send_message_to_author(self, content: str):
        if self.config.debug_mode:
            print(f"{content}")
            return

        actor_id = self.elem.creator.actor_id

        self.lemmy_http.send_message(actor_id, f"{content}\n\nMod bot (with L plates)")

    def post_comment(self, content: str):
        if self.config.debug_mode:
            print(f"{content}")
            return

        self.lemmy.create_comment(
            f"{content}\n\nMod bot (with L plates)",
            self.elem.post.id
        )

    def remove_thing(self, reason: str):
        if self.config.debug_mode:
            print(f"Remove {reason}")
            return
        if isinstance(self.elem, PostView):
            self.lemmy.remove_post(
                self.elem.post.id,
                True,
                reason
            )
        elif isinstance(self.elem, CommentView):
            self.lemmy.remove_comment(
                self.elem.comment.id,
                True,
                reason
            )

    def _get_url(self) -> Optional[str]:
        if not(isinstance(self.elem, PostView)) or self.elem.post.url is None:
            return None
        return self.elem.post.url

    def fetch_image(self, url: str = None) -> (Image, str):
        if url is None:
            url = self._get_url()
        try:
            img = Image.open(BytesIO(requests.get(url).content))
            return img, str(imagehash.phash(img))
        except UnidentifiedImageError:
            return None, None

    def fetch_content(self, url: str = None) -> (bytes, Dict[str, str]):
        if url is None:
            url = self._get_url()

        cont = requests.get(
            url,
            allow_redirects=True,
            headers={
                "Accepts": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0"
            }
        )
        return cont.content, cont.headers

    def send_message(self, message):
        if self.matrix_facade is None:
            return
        self.matrix_facade.send_message(
            self.config.matrix_config.room_id,
            message + "\n\nMod bot (with L plates)"
        )


class ContentType:
    POST_TITLE = 0
    POST_BODY = 1
    POST_LINK = 2
    COMMENT = 3


class Content:
    community: str
    content: str
    actor_id: str
    link_to_content: str
    type: ContentType

    def __init__(self, community: str, content: str, actor_id: str, link_to_content: str, type: ContentType):
        self.community = community
        self.content = content
        self.actor_id = actor_id
        self.link_to_content = link_to_content
        self.type = type


class ContentResult:
    flags: List[str]
    extras: Optional[Any]
    was_deleted: bool

    def __init__(self, flags: List[str], extras: Optional[Any], was_deleted: bool = False):
        self.flags = flags
        self.extras = extras
        self.was_deleted = was_deleted

    @staticmethod
    def nothing():
        return ContentResult([], None)


class Processor:

    def setup(self) -> None:
        pass

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        return ContentResult.nothing()



