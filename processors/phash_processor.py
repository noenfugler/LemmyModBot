from io import BytesIO

import requests
from PIL import Image
import imagehash

from processors import Processor, Content, LemmyHandle, ContentResult
from processors.base import ContentType


class PhashProcessor(Processor):

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        if content.type != ContentType.POST_LINK:
            return ContentResult.nothing()

        phash = handle.database.url_exists(content.content)
        if phash is not None:
            return self._warn_user(handle, phash)

        phash = str(imagehash.phash(Image.open(BytesIO(requests.get(content.content).content))))
        if handle.database.phash_exists(phash):
            handle.database.add_phash(content.content, phash)
            return self._warn_user(handle, phash)

        handle.database.add_phash(content.content, phash)

        return ContentResult([], {"phash": phash})

    def _warn_user(self, handle: LemmyHandle, phash: str) -> ContentResult:
        posts = handle.database.get_post_links_by_phash(phash)
        other_posts = ', '.join([f"[link]({post})" for post in posts])
        handle.post_comment(f"This post appears to be a duplicate of the following post{ '' if len(posts) == 1 else 's' }: {other_posts}. "
                            f"This could be a false positive (beep boop I am a robot).")
        return ContentResult([], {"phash": phash})
