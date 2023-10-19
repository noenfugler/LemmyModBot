import urllib.parse
from typing import Union, Optional

from pylemmy import Lemmy
from pylemmy.api.utils import BaseApiModel
from pylemmy.endpoints import LemmyAPI

from lemmymodbot.api import LemmyModAPI, PostMessage, PostRemovePost, PostRemoveComment


class LemmyModHttp:

    def __init__(self, lemmy: Lemmy):
        self.lemmy = lemmy

    def send_message(self, recipient_id: int, content: str):
        payload = PostMessage(
            auth=self.lemmy.get_token(),
            content=content,
            recipient_id=recipient_id,
        )
        response = self.lemmy.post_request(LemmyModAPI.PostMessage, params=payload)
        response.raise_for_status()

    def remove_post(self, post_id: int, reason: Optional[str] = None):
        payload = PostRemovePost(
            auth=self.lemmy.get_token(),
            post_id=post_id,
            reason=reason
        )
        response = self.lemmy.post_request(LemmyModAPI.RemovePost, params=payload)
        response.raise_for_status()

    def remove_comment(self, comment_id: int, reason: Optional[str] = None):
        payload = PostRemoveComment(
            auth=self.lemmy.get_token(),
            comment_id=comment_id,
            reason=reason
        )
        response = self.lemmy.post_request(LemmyModAPI.RemoveComment, params=payload)
        response.raise_for_status()

    def delete_request(
        self,
        path: Union[LemmyAPI, LemmyModAPI],
        params: Optional[BaseApiModel] = None,
    ):
        response = self.lemmy.session.delete(
            self._get_url(path),
            params=params.dict() if params is not None else {},
            timeout=self.lemmy.request_timeout,
        )
        return response.json()

    def _get_url(self, path: Union[LemmyAPI, LemmyModAPI]):
        return urllib.parse.urljoin(self.lemmy.lemmy_url, path.value)

