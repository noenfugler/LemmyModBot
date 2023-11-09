from typing import List, Optional

from magic import Magic

from lemmymodbot.processors import Processor, Content, LemmyHandle, ContentResult
from lemmymodbot.processors.base import ContentType


class MimeProcessor(Processor):
    match: List[str]
    # Refers to type, as in type/subtype
    type: Optional[List[str]]

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        if content.type != ContentType.POST_LINK:
            return ContentResult.nothing()

        file, headers = handle.fetch_content(content.content)
        mime = Magic(mime=True).from_buffer(file)
        components = mime.split("/")
        return self.handle(mime in self.match, self.type is not None and components[0] in self.type, mime)

    def handle(self, in_match_list: bool, in_type_list: bool, mime: str) -> ContentResult:
        pass


class MimeWhitelistProcessor(MimeProcessor):

    def __init__(self, whitelist: Optional[List[str]] = None, type_whitelist: Optional[List[str]] = None):
        if whitelist is None:
            whitelist = []
        self.match = whitelist
        self.type = type_whitelist

    def handle(self, in_match_list: bool, in_type_list: bool, mime: str) -> ContentResult:
        return ContentResult([] if in_match_list or in_type_list else ["not_whitelisted_mime"], {"mime": mime})


class MimeBlacklistProcessor(MimeProcessor):
    def __init__(self, blacklist: Optional[List[str]] = None):
        if blacklist is None:
            blacklist = []
        self.match = blacklist

    def handle(self, in_match_list: bool, in_type_list: bool, mime: str) -> ContentResult:
        return ContentResult(["blacklisted_mime"] if in_match_list else [], {"mime": mime})
