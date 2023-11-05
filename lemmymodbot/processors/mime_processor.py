
from typing import List, Any

import requests
import torchtext

from lemmymodbot.processors import Processor, Content, LemmyHandle, ContentResult
from lemmymodbot.processors.base import ContentType


class MimeWhitelistProcessor(Processor):
    whitelist: List[str]

    def __init__(self, whitelist: List[str]):
        self.whitelist = whitelist

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        if content.type != ContentType.POST_LINK:
            return ContentResult.nothing()

        r = requests.head(content.content)
        if r.headers["content-type"] not in self.whitelist:
            return ContentResult(["not_whitelisted_mime"], {"mime": r.headers["content-type"]})

        return ContentResult.nothing()
