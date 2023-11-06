import os

from lemmymodbot import PhotoDNAClient
from lemmymodbot.processors import Processor, Content, LemmyHandle, ContentResult
from lemmymodbot.processors.base import ContentType


class PhotoDNAProcessor(Processor):
    client: PhotoDNAClient

    def setup(self) -> None:
        self.client = PhotoDNAClient(os.getenv("PHOTODNA_API"))

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        if content.type != ContentType.POST_LINK:
            return ContentResult.nothing()

        if self.client.check_url(content.content).is_match:
            return self._delete_and_warn(handle, content)

        return ContentResult.nothing()

    def _delete_and_warn(self, handle: LemmyHandle, content: Content) -> ContentResult:
        handle.remove_thing("CSAM content detected")
        handle.send_message(
            f"""!!! Important !!!\nCSAM content was detected in the following post:
            {content.link_to_content}. Please collect metadata on the user and submit a report!"""
        )
        return ContentResult(["csam"], {"csam": "True"}, True)
