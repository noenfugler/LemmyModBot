from typing import List, Any

import torchtext

from lemmymodbot.processors import Processor, Content, LemmyHandle, ContentResult
from lemmymodbot.processors.base import ContentType


class BlacklistProcessor(Processor):
    blacklist: List[str]
    tokenizer: Any

    def __init__(self, blacklist: List[str]):
        self.blacklist = blacklist

    def setup(self) -> None:
        self.tokenizer = torchtext.data.utils.get_tokenizer("basic_english")

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        if content.type == ContentType.POST_LINK:
            return ContentResult.nothing()

        tokens = self.tokenizer(content.content.lower())
        if any(x in self.blacklist for x in tokens):
            return ContentResult(['word_blacklist'], None)
        return ContentResult.nothing()
