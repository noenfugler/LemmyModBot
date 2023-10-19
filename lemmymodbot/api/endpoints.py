from enum import Enum

from pylemmy.endpoints import base_api_path


class LemmyModAPI(Enum):
    PostMessage = base_api_path + "private_message"
    RemovePost = base_api_path + "post/remove"
    RemoveComment = base_api_path + "comment/remove"
