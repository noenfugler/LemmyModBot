from sqlalchemy import select
from sqlalchemy.orm import Session

from lemmymodbot.data.base import CurrentPage, session_scope


class MonitorPersistence:

    def _get_page_entry(self, community_name: str, session: Session) -> CurrentPage:
        return (session.execute(select(CurrentPage).filter(CurrentPage.community_name == community_name))
                .scalar_one_or_none())

    def get_current_page(self, community_name: str) -> int:
        pass

    def set_current_page(self, community_name: str, page_number: int):
        pass


class PostMonitorPersistence(MonitorPersistence):

    def get_current_page(self, community_name: str) -> int:
        with session_scope() as session:
            result = self._get_page_entry(community_name, session)
            if result is None:
                return 1
            return result.post_page

    def set_current_page(self, community_name: str, page_number: int):
        with session_scope() as session:
            current = self._get_page_entry(community_name, session)
            if current is None:
                session.add(CurrentPage(
                    community_name=community_name,
                    post_page=page_number,
                    comment_page=1
                ))
            else:
                current.post_page = page_number


class CommentMonitorPersistence(MonitorPersistence):

    def get_current_page(self, community_name: str) -> int:
        with session_scope() as session:
            result = self._get_page_entry(community_name, session)
            if result is None:
                return 1
            return result.comment_page

    def set_current_page(self, community_name: str, page_number: int):
        with session_scope() as session:
            current = self._get_page_entry(community_name, session)
            if current is None:
                session.add(CurrentPage(
                    community_name=community_name,
                    post_page=1,
                    comment_page=page_number
                ))
            else:
                current.comment_page = page_number
