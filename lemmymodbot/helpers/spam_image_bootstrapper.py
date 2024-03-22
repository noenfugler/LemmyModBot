from typing import List, Callable

from PIL.Image import Image

from lemmymodbot.database import Database
from lemmymodbot.helpers import fetch_image


class SpamImageBootstrapper:
    database: Database
    fetch_image: Callable[[str], tuple[Image, str]]

    def __init__(self, database: Database, fetch_image: Callable[[str], tuple[Image, str]] = fetch_image):
        self.database = database
        self.fetch_image = fetch_image

    def setup(self, images: List[str]):
        for image in images:
            is_url = image.startswith("http")
            if is_url:
                # Check if url has already been added
                phash = self.database.url_exists(image)
                if phash is not None:
                    if self.database.phash_exists(phash, True):
                        continue

            phash = self.fetch_image(image)[1] if is_url else image
            if phash is not None:
                if self.database.phash_exists(phash, True):
                    continue

                self.database.add_phash(image if is_url else "", phash, True)
