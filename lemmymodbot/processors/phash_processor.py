from lemmymodbot.processors import Processor, Content, LemmyHandle, ContentResult
from lemmymodbot.processors.base import ContentType


class PhashProcessor(Processor):

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        if content.type != ContentType.POST_LINK:
            return ContentResult.nothing()

        phash = handle.database.url_exists(content.content)
        if phash is not None:
            return self._warn_user(handle, phash)

        phash = handle.fetch_image(content.content)[1]
        if phash is None:
            return ContentResult.nothing()
        
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
