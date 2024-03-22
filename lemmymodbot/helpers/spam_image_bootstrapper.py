from typing import List

from lemmymodbot.database import Database
from lemmymodbot.helpers import fetch_image


class SpamImageBootstrapper:
    database: Database

    def __init__(self, database: Database):
        self.database = database

    def setup(self, images: List[str]):
        for image in images:
            # Check if url has already been added
            phash = self.database.url_exists(image)
            if phash is not None:
                if self.database.phash_exists(phash, True):
                    continue

            phash = fetch_image(image)[1]
            if phash is not None:
                if self.database.phash_exists(phash, True):
                    continue

                self.database.add_phash(image, phash, True)
