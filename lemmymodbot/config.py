# Rename this file to config.py and update the values below.
import os
from typing import List


class MatrixConfig:
    server: str
    account: str
    password: str
    room_id: str

    def __init__(
            self,
            server: str,
            account: str,
            password: str,
            room_id: str,
    ):
        self.server = server
        self.account = account
        self.password = password
        self.room_id = room_id


class Config:
    username: str
    password: str
    instance: str
    owner_username: str
    communities: List[str]
    debug_mode: bool
    matrix_config: MatrixConfig
    spam_images: List[str]

    def __init__(
            self,
            username: str,
            password: str,
            instance: str,
            owner_username: str,
            communities: List[str],
            matrix_config: MatrixConfig = None,
            spam_images: List[str] = None,
            debug_mode: bool = False,
    ):
        self.username = username
        self.password = password
        self.instance = instance
        self.owner_username = owner_username
        self.communities = communities
        self.debug_mode = debug_mode
        self.matrix_config = matrix_config
        self.spam_images = spam_images


def environment_config():
    return Config(
        os.getenv("LEMMY_USERNAME"),
        os.getenv("LEMMY_PASSWORD"),
        os.getenv("LEMMY_INSTANCE"),
        os.getenv("LEMMY_OWNER_USERNAME"),
        [x.strip() for x in os.getenv("LEMMY_COMMUNITIES").split(',')],
        MatrixConfig(
            os.getenv("MATRIX_INSTANCE"),
            os.getenv("MATRIX_USERNAME"),
            os.getenv("MATRIX_PASSWORD"),
            os.getenv("MATRIX_ROOM")
        ) if os.getenv("MATRIX_INSTANCE") is not None else None,
        [x.strip() for x in os.getenv("SPAM_IMAGES").split(',')] if os.getenv("SPAM_IMAGES") is not None else [],
        os.getenv("DEBUG") == "True"
    )
