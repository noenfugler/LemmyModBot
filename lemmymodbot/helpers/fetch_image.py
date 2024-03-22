from io import BytesIO

import requests
from PIL import Image, UnidentifiedImageError
import imagehash


def fetch_image(url: str) -> (Image, str):
    try:
        img = Image.open(BytesIO(requests.get(url).content))
        return img, str(imagehash.phash(img))
    except UnidentifiedImageError:
        return None, None