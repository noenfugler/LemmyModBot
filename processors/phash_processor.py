from io import BytesIO

import requests
from PIL import Image

from processors import Processor, Content, LemmyHandle, ContentResult
from processors.processor import ContentType


class PhashProcessor(Processor):
    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        if content.type != ContentType.POST_LINK:
            return ContentResult.nothing()

        # if content

        img = Image.open(BytesIO(requests.get(content.content).content))

        return super().execute(content, handle)

    def warn_user(self, handle: LemmyHandle):

