""" This file creates and manages a bot to help Moderate one or more Lemmy communities."""

import traceback
from time import sleep
from typing import Union, List
import logging
import sys
from pprint import pprint

from pylemmy import Lemmy
from pylemmy.models.post import Post
from pylemmy.models.comment import Comment

from . import MatrixFacade
from .config import Config, environment_config
from lemmymodbot.processors.base import Processor, Content, ContentType, LemmyHandle
from .reconnection_manager import ReconnectionDelayManager
from .database import Database


class LemmyBot:
    processors: List[Processor]
    config: Config
    matrix_facade: MatrixFacade
    """ LemmyBot is a bot that checks Lemmy posts and comments for toxicity, as well as
    performing regexp matching, user watchlist monitoring amongst other things."""

    def __init__(
            self,
            processors: List[Processor],
            config: Config = None
    ):
        self.config = config if config is not None else environment_config()
        self.processors = processors
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        for processor in self.processors:
            processor.setup()

        self.lemmy = Lemmy(
            lemmy_url=self.config.instance,
            username=self.config.username,
            password=self.config.password,
            user_agent="custom user agent (by " + self.config.owner_username + ")",
        )

        db_directory_name = 'data'
        db_file_name = 'history.db'
        self.history_db = Database(db_directory_name, db_file_name)
        self.logger.info("Bot starting!")
        self.mydelay = ReconnectionDelayManager(logger=self.logger)
        self.matrix_facade = MatrixFacade(
            self.config.matrix_config.server,
            self.config.matrix_config.account,
            self.config.matrix_config.password
        ) if self.config is not None and self.config.matrix_config is not None else None

    def clean_content(self, content: str):
        if content is None:
            return None

        """Tidy up content to remove unwanted characters before processing text"""

        content = content.replace("\n\r", " ")
        content = content.replace("\n", " ")
        content = content.replace("\r", " ")
        content = content.replace("\t", ' ')
        content = content.replace("<br>", " ")
        return content

    def run_processors(self, content: Content, elem: Union[Post, Comment], flags: List[str], extras):
        for processor in self.processors:
            result = processor.execute(content, LemmyHandle(
                self.lemmy,
                elem,
                self.history_db,
                self.config,
                self.matrix_facade
            ))
            if result.flags is not None:
                flags += result.flags
            if result.extras is not None:
                extras = {**extras, **result.extras}

        return flags, extras

    def process_comment(self, elem):
        """Determine if the comment is new and if so run through detoxifier.  If toxic, then rrt.
        Update database accordingly"""

        comment_id = elem.comment_view.comment.id
        self.logger.info('COMMENT %s: %s', comment_id, elem.comment_view.comment.content)
        if self.history_db.in_comments_list(comment_id):
            self.logger.info('Comment Already Assessed')
            return

        flags = []
        extras = {}

        content = Content(
            elem.comment_view.community.name,
            self.clean_content(elem.comment_view.comment.content),
            elem.comment_view.creator.actor_id,
            elem.comment_view.comment.path,
            ContentType.COMMENT
        )

        flags, extras = self.run_processors(content, elem, flags, extras)

        self.history_db.add_to_comments_list(comment_id, extras)
        pprint(vars(elem))

        if len(flags) <= 0:
            self.history_db.add_outcome_to_comment(comment_id, "No report")

        # we found something bad
        self.logger.info('REPORT FOR COMMENT: %s', flags)
        # noinspection PyBroadException
        try:
            if not self.config.debug_mode:
                elem.create_report(reason='Mod bot (with L plates) : ' + ', '.join(flags))
            self.logger.info('****************\nREPORTED COMMENT\n******************')
            self.history_db.add_outcome_to_comment(comment_id, "Reported comment for: "
                                                   + '|'.join(flags))
        except Exception:
            self.logger.error("ERROR: UNABLE TO CREATE REPORT", exc_info=True)
            self.history_db.add_outcome_to_comment(comment_id, "Failed to report comment for: "
                                                   + '|'.join(flags) + " due to exception :"
                                                   + traceback.format_exc())
        if self.matrix_facade is not None:
            self.matrix_facade.send_message(
                self.config.matrix_config.room_id,
                self.matrix_facade.report(flags, extras, str(elem.comment_view.comment))
            )

        sleep(5)

    def process_post(self, elem):
        """Determine if the post is new and if so run through detoxifier.  If toxic, then report.
        Update database accordingly"""

        post_id = elem.post_view.post.id
        self.logger.info('POST %s: %s', post_id, elem.post_view.post.name)
        if self.history_db.in_posts_list(post_id):
            self.logger.info('Post Already Assessed')
            return

        flags = []
        extras_title = {}
        extras_body = {}
        extras = {}

        title_content = Content(
            elem.post_view.community.name,
            self.clean_content(elem.post_view.post.name),
            elem.post_view.creator.actor_id,
            elem.post_view.post.url,
            ContentType.POST_TITLE
        )
        body_content = Content(
            elem.post_view.community.name,
            self.clean_content(elem.post_view.post.body),
            elem.post_view.creator.actor_id,
            elem.post_view.post.url,
            ContentType.POST_BODY
        )
        link_content = Content(
            elem.post_view.community.name,
            elem.post_view.post.url,
            elem.post_view.creator.actor_id,
            elem.post_view.post.url,
            ContentType.POST_LINK
        )

        flags, extras_title = self.run_processors(title_content, elem, flags, extras_title)
        if body_content.content is not None:
            flags, extras_body = self.run_processors(body_content, elem, flags, extras_body)
        if link_content.content is not None:
            flags, extras = self.run_processors(link_content, elem, flags, extras)

        self.history_db.add_to_posts_list(
            post_id,
            extras_title,
            extras_body,
            extras,
            f"{self.config.instance}/post/{elem.post_view.post.id}"
        )
        pprint(elem)
        if len(flags) <= 0:
            self.history_db.add_outcome_to_post(post_id, "No report")
            return

        self.logger.info('REPORT FOR POST: %s', flags)
        # noinspection PyBroadException
        try:
            if not self.config.debug_mode:
                elem.create_report(reason='Mod bot (with L plates) : ' + ', '.join(flags))
            self.logger.info('****************\nREPORTED POST\n******************')
            self.history_db.add_outcome_to_post(post_id, "Reported Post for: "
                                                + '|'.join(flags))
        except Exception:
            self.logger.error("ERROR: UNABLE TO CREATE REPORT", exc_info=True)
            self.history_db.add_outcome_to_comment(post_id, "Failed to report post for: "
                                                   + '|'.join(flags) + " due to exception :"
                                                   + traceback.format_exc())
        if self.matrix_facade is not None:
            self.matrix_facade.send_message(
                self.config.matrix_config.room_id,
                self.matrix_facade.report(flags, extras, str(elem.post_view.post))
            )
        sleep(5)

    def process_content(self, elem: Union[Post, Comment]):
        """ the main doing function, called when a new post or comment is received"""

        if isinstance(elem, Comment):
            # It's a comment!
            self.process_comment(elem)
        elif isinstance(elem, Post):
            # It's a post
            self.process_post(elem)
        # sleep(5)

    def run(self):
        """This is the main run loop for the bot.  It should be called after initiation of bot"""
        while True:
            # noinspection PyBroadException
            try:
                multi_stream = self.lemmy.multi_communities_stream(self.config.communities)
                multi_stream.content_apply(self.process_content)
            except Exception:
                self.logger.error("Exception raised!", exc_info=True)
                self.mydelay.wait()
