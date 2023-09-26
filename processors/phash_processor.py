from io import BytesIO

import requests
from PIL import Image
import imagehash

from processors import Processor, Content, LemmyHandle, ContentResult
from processors.base import ContentType


class PhashProcessor(Processor):

    def __init__(self, message: str):
        self.message = message

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        if content.type != ContentType.POST_LINK:
            return ContentResult.nothing()

        if handle.database.url_exists(content.content):
            return self._warn_user(handle)

        phash = str(imagehash.phash(Image.open(BytesIO(requests.get(content.content).content))))
        if handle.database.phash_exists(phash):
            return self._warn_user(handle)

        handle.database.add_phash(content.content, phash)

        return ContentResult.nothing()

    def _warn_user(self, handle: LemmyHandle) -> ContentResult:
        handle.post_comment(self.message)
        return ContentResult.nothing()
