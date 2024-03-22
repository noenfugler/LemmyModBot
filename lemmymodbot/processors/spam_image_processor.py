from typing import List

from lemmymodbot.processors import Processor, Content, LemmyHandle, ContentResult
from lemmymodbot.processors.base import ContentType
from lemmymodbot.helpers import extract_links_from_markdown


class SpamImageProcessor(Processor):
    hashes: List[str]

    def __init__(self, hashes: List[str]):
        self.hashes = hashes

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        result = False
        if content.type == ContentType.POST_LINK:
            result = self._run_check(content.content, handle)
        elif content.type == ContentType.POST_BODY or content.type == ContentType.COMMENT:
            links = extract_links_from_markdown(content.content)
            for link in links:
                result = self._run_check(link, handle)
                if result:
                    break

        if not result:
            return ContentResult.nothing()

        handle.remove_thing("Spam image detected")

        return ContentResult.nothing()

    def _run_check(self, url: str, handle: LemmyHandle) -> bool:
        phash = handle.fetch_image(url)[1]
        if phash is None:
            return False

        return phash in self.hashes
