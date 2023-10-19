from typing import Optional

from pylemmy.api.utils import BaseApiModel


class PostMessage(BaseApiModel):
    auth: str = None
    content: str = None
    recipient_id: int = None


class PostRemovePost(BaseApiModel):
    auth: str = None
    post_id: str = None
    removed: bool = True
    reason: Optional[str] = None


class PostRemoveComment(BaseApiModel):
    auth: str = None
    comment_id: str = None
    removed: bool = True
    reason: Optional[str] = None
