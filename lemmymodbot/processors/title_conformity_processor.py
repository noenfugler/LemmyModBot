import re

from lemmymodbot.processors import Processor, Content, LemmyHandle, ContentResult
from lemmymodbot.processors.base import ContentType


class TitleConformityProcessor(Processor):
    message: str

    def __init__(self, regex: str, message: str):
        self.pattern = re.compile(regex)
        self.message = message

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        if content.type != ContentType.POST_TITLE:
            return ContentResult.nothing()

        if not self.pattern.match(content.content):
            handle.post_comment(self.message)

        return ContentResult.nothing()
