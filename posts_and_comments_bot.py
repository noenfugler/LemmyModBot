""" This file creates and manages to bot.
TODO:  Move main content to a separate library"""

import traceback
from time import sleep
import os
from pathlib import Path
import sqlite3
from typing import Union
from datetime import datetime

from pylemmy import Lemmy
from pylemmy.models.post import Post
from pylemmy.models.comment import Comment
from detoxify import Detoxify
import credentials


class Database:
    """ Object to handle the interactions with the SQLite database"""

    def __init__(self, directory_name, filename):
        """ a class to handle the database connection and queries"""
        self.db_location = directory_name + "/" + filename
        my_directory = Path(directory_name)
        if not my_directory.is_dir():
            os.makedirs(directory_name)
        create_comments_table_sql = '''CREATE TABLE "comments" (
                                        "id"	INTEGER NOT NULL UNIQUE,
                                        "toxicity"	REAL,
                                        "severe_toxicity"	REAL,
                                        "obscene"	REAL,
                                        "identity_attack"	REAL,
                                        "insult"	REAL,
                                        "threat"	REAL,
                                        "sexual_explicit"	REAL,
                                        "outcome" TEXT,
                                        PRIMARY KEY("id")
        );'''
        self.check_table_exists('comments', create_comments_table_sql)
        create_posts_table_sql = '''CREATE TABLE "posts" (
                                "id"	INTEGER NOT NULL UNIQUE,
                                "name_toxicity"	REAL,
                                "name_severe_toxicity"	REAL,
                                "name_obscene"	REAL,
                                "name_identity_attack"	REAL,
                                "name_insult"	REAL,
                                "name_threat"	REAL,
                                "name_sexual_explicit"	REAL,
                                "body_toxicity"	REAL,
                                "body_severe_toxicity"	REAL,
                                "body_obscene"	REAL,
                                "body_identity_attack"	REAL,
                                "body_insult"	REAL,
                                "body_threat"	REAL,
                                "body_sexual_explicit"	REAL,
                                "outcome"	TEXT,
                                PRIMARY KEY("id"));'''
        self.check_table_exists('posts', create_posts_table_sql)

    def check_table_exists(self, table_name, create_sql):
        """ check if comments table exists"""
        # connect to database
        conn = sqlite3.connect(self.db_location)
        # create cursor object
        cur = conn.cursor()
        # generate list of tables with the name of the table
        sql = f"""SELECT tbl_name FROM sqlite_master WHERE type='table'
            AND tbl_name='{table_name}'; """
        list_of_tables = cur.execute(sql).fetchall()
        if len(list_of_tables) == 0:
            # table does not yet exist.  Create it
            cur.execute(create_sql)
        # commit changes
        conn.commit()
        # terminate the connection
        conn.close()

    def in_comments_list(self, comment_id):
        """check whether this comment (comment_id) is stored in
        the database as having been previously checked"""
        conn = sqlite3.connect(self.db_location)
        found = False
        result = conn.execute(f'SELECT count(id) FROM comments WHERE id={comment_id};')
        for row in result.fetchone():
            if row != 0:
                found = True
        conn.close()
        return found

    def in_posts_list(self, post_id):
        """ check whether this post (id) is stored in
        the database as having been previously checked"""

        conn = sqlite3.connect(self.db_location)
        found = False
        result = conn.execute(f'SELECT count(id) FROM posts WHERE id={post_id};')
        for row in result.fetchone():
            if row != 0:
                found = True
        conn.close()
        return found

    def add_to_comments_list(self, comment_id, results):
        """ add a comment id to the list of previously checked comments in the database """

        conn = sqlite3.connect(self.db_location)
        sql = f'''INSERT INTO comments(id, toxicity, severe_toxicity, obscene, identity_attack, 
        insult, threat, sexual_explicit) VALUES{comment_id, results['toxicity'],
        results['severe_toxicity'], results['obscene'], results['identity_attack'],
        results['insult'], results['threat'], results['sexual_explicit']};'''
        # try:
        conn.execute(sql)
        conn.commit()
        conn.close()

    def add_outcome_to_comment(self, comment_id, outcome):
        """ add an outcome to a comment record in the database """

        conn = sqlite3.connect(self.db_location)
        # tidy up the outcome string to remove quotes which might break the SQL statement
        outcome = outcome.replace('"', '')
        outcome = outcome.replace("'", "")
        sql = f'''UPDATE comments SET outcome='{outcome}' WHERE id={comment_id};'''
        conn.execute(sql)
        conn.commit()
        conn.close()

    def add_outcome_to_post(self, post_id, outcome):
        """ add an outcome to a post record in the database """

        conn = sqlite3.connect(self.db_location)
        sql = f'''UPDATE posts SET outcome='{outcome}' WHERE id={post_id};'''
        conn.execute(sql)
        conn.commit()
        conn.close()

    def add_to_posts_list(self, post_id, name_results, body_results):
        """ add a post id to the list of previously checked posts """

        conn = sqlite3.connect(self.db_location)
        sql = f"""INSERT INTO posts(id, name_toxicity, name_severe_toxicity, name_obscene, 
        name_identity_attack, name_insult, name_threat, name_sexual_explicit, body_toxicity, 
        body_severe_toxicity, body_obscene, body_identity_attack, body_insult, body_threat, 
        body_sexual_explicit) VALUES{post_id, name_results['toxicity'], 
        name_results['severe_toxicity'], name_results['obscene'], name_results['identity_attack'],
        name_results['insult'], name_results['threat'], name_results['sexual_explicit'], 
        body_results['toxicity'], body_results['severe_toxicity'], body_results['obscene'], 
        body_results['identity_attack'], body_results['insult'], body_results['threat'], 
        body_results['sexual_explicit']};"""

        conn.execute(sql)
        conn.commit()
        conn.close()


def assess_content_toxicity(content):
    """Process content using Detoxify and return results as a dictionary"""
    flags = []
    if content is not None:
        results = Detoxify('unbiased').predict(content)
        print(results)
        total = results['toxicity'] + \
            results['severe_toxicity'] + \
            results['obscene'] + \
            results['identity_attack'] + \
            results['insult'] + \
            results['threat'] + \
            results['sexual_explicit']
        print(total)
        if results['toxicity'] > credentials.toxicity and total > credentials.total:
            flags.append('toxicity')
        if results['severe_toxicity'] > credentials.severe_toxicity and total > credentials.total:
            flags.append('severe_toxicity')
        if results['obscene'] > credentials.obscene and total > credentials.total:
            flags.append('obscene')
        if results['identity_attack'] > credentials.identity_attack and total > credentials.total:
            flags.append('identity_attack')
        if results['insult'] > credentials.insult and total > credentials.total:
            flags.append('insult')
        if results['threat'] > credentials.threat and total > credentials.total:
            flags.append('threat')
        if results['sexual_explicit'] > credentials.sexually_explicit and total > credentials.total:
            flags.append('sexual_explicit')

    else:
        results = {"toxicity": 0.0, "severe_toxicity": 0.0, "obscene": 0.0, "identity_attack": 0.0,
                   "insult": 0.0, "threat": 0.0, "sexual_explicit": 0.0}
    return results


def process_comment(elem):
    """Determine if the comment is new and if so run through detoxifier.  If toxic, then report.
    Update database accordingly"""

    comment_id = elem.comment_view.comment.id
    print(f'\nCOMMENT {comment_id}:', elem.comment_view.comment.content)
    if comment_id == 1123305:
        pass
    if not db.in_comments_list(comment_id):
        flags = []
        content = elem.comment_view.comment.content
        actor_id = elem.comment_view.creator.actor_id

        print(datetime.now().isoformat())
        results = assess_content_toxicity(content)

        if actor_id in credentials.user_watch_list:
            flags.append('user_watch_list')

        db.add_to_comments_list(comment_id, results)
        if len(flags) > 0:
            # we found something bad
            print('***')
            print('REPORT FOR COMMENT:')
            print(flags)
            print('***\n')
            try:
                elem.create_report(reason='Detoxify bot: ' + ', '.join(flags))
                print('****************\nREPORTED COMMENT\n******************')
                db.add_outcome_to_comment(comment_id, "Reported comment for: " + '|'.join(flags))
            except Exception as exception_create_comment_report:
                print(exception_create_comment_report)
                print("ERROR: UNABLE TO CREATE REPORT")
                print(traceback.format_exc())
                db.add_outcome_to_comment(comment_id, "Failed to report comment for: " + '|'.join(
                    flags) + " due to exception :" + traceback.format_exc())
        else:
            db.add_outcome_to_comment(comment_id, "No report")
    else:
        print('Already Assessed')


def process_post(elem):
    """Determine if the post is new and if so run through detoxifier.  If toxic, then report.
    Update database accordingly"""

    post_id = elem.post_view.post.id
    print(f'\nPOST {post_id}:', elem.post_view.post.name)
    if post_id == 638082:
        pass
    if not db.in_posts_list(post_id):
        flags = []
        name = elem.post_view.post.name
        body = elem.post_view.post.body
        actor_id = elem.post_view.creator.actor_id

        print(datetime.now().isoformat())
        name_results = assess_content_toxicity(name)
        body_results = assess_content_toxicity(body)

        if actor_id in credentials.user_watch_list:
            flags.append('user_watch_list')

        db.add_to_posts_list(post_id, name_results, body_results)
        if len(flags) > 0:
            print('***')
            print('REPORT FOR COMMENT:')
            print(flags)
            print('***\n')
            try:
                elem.create_report(reason='Detoxify bot: ' + ', '.join(flags))
                print('****************\nREPORTED POST\n******************')
                db.add_outcome_to_post(post_id, "Reported Post for: " + '|'.join(flags))
            except Exception as exception_create_post_report:
                print(exception_create_post_report)
                print("ERROR: UNABLE TO CREATE REPORT")
                db.add_outcome_to_comment(post_id, "Failed to report post for: " + '|'.join(
                    flags) + " due to exception :" + traceback.format_exc())
            # pass
        else:
            db.add_outcome_to_post(post_id, "No report")

    else:
        print('Already Assessed')


def process_content(elem: Union[Post, Comment]):
    """ the main doing function, called when a new post or comment is received"""

    if isinstance(elem, Comment):
        # It's a comment!
        process_comment(elem)
    elif isinstance(elem, Post):
        # It's a post
        process_post(elem)


lemmy = Lemmy(
    lemmy_url=credentials.instance,
    username=credentials.username,
    password=credentials.password,
    user_agent="custom user agent (by " + credentials.alt_username + ")",
)

if __name__ == '__main__':
    DB_DIRECTORY_NAME = 'history'
    DB_FILE_NAME = 'history.db'
    db = Database(DB_DIRECTORY_NAME, DB_FILE_NAME)
    while True:
        multi_stream = lemmy.multi_communities_stream(credentials.communities)
        try:
            multi_stream.content_apply(process_content)
        except Exception as exception_process_content:
            print(exception_process_content)
            print('Error in connection, stream or process_content.  Waiting 30s and trying again')
            sleep(30)
