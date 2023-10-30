import os
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from sqlite3 import Error
from typing import Optional, List


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
                                        "non_toxicity"	REAL,
                                        "outcome" TEXT,
                                        PRIMARY KEY("id")
        );'''
        self.check_table_exists('comments', create_comments_table_sql)
        create_posts_table_sql = '''CREATE TABLE "posts" (
                                "id"	INTEGER NOT NULL UNIQUE,
                                "name_toxicity"	REAL,
                                "name_non_toxicity"	REAL,
                                "body_toxicity"	REAL,
                                "body_non_toxicity"	REAL,
                                "outcome"	TEXT,
                                "phash" TEXT,
                                "link" TEXT,
                                PRIMARY KEY("id"));'''
        self.check_table_exists('posts', create_posts_table_sql)
        self.update_table('''ALTER TABLE "posts" ADD COLUMN "phash" TEXT''')
        self.update_table('''ALTER TABLE "posts" ADD COLUMN "link" TEXT''')
        create_phash_table_sql = '''CREATE TABLE "phash" (
            "url" STRING NOT NULL UNIQUE,
            "phash" STRING NOT NULL,
            PRIMARY KEY("url")
        );'''
        self.check_table_exists('phash', create_phash_table_sql)

    @contextmanager
    def _session(self):
        session = sqlite3.connect(self.db_location)
        try:
            yield session
            session.commit()
        except Error:
            session.rollback()
            raise
        finally:
            session.close()

    def check_table_exists(self, table_name, create_sql):
        """ check if comments table exists"""
        # connect to database
        with self._session() as conn:
            # create cursor object
            cur = conn.cursor()
            # generate list of tables with the name of the table
            sql = """SELECT tbl_name FROM sqlite_master WHERE type='table'
                AND tbl_name=?; """
            list_of_tables = cur.execute(sql, (table_name,)).fetchall()
            if len(list_of_tables) == 0:
                # table does not yet exist.  Create it
                cur.execute(create_sql)

    def update_table(self, sql):
        with self._session() as conn:
            try:
                conn.execute(sql)
            except Error:
                pass

    def in_comments_list(self, comment_id):
        """check whether this comment (comment_id) is stored in
        the database as having been previously checked"""
        with self._session() as conn:
            result = conn.execute('SELECT count(id) FROM comments WHERE id=?;', (comment_id,))
            for row in result.fetchone():
                if row != 0:
                    return True
            return False

    def in_posts_list(self, post_id):
        """ check whether this post (id) is stored in
        the database as having been previously checked"""
        with self._session() as conn:
            result = conn.execute('SELECT count(id) FROM posts WHERE id=?;', (post_id,))
            for row in result.fetchone():
                if row != 0:
                    return True
        return False

    def add_to_comments_list(self, comment_id, results):
        """ add a comment id to the list of previously checked comments in the database """
        with self._session() as conn:
            sql = '''INSERT INTO comments(id, toxicity, non_toxicity) VALUES(?,?,?);'''
            conn.execute(sql, (comment_id, results['toxicity'], results['non_toxicity']))

    def add_outcome_to_comment(self, comment_id, outcome):
        """ add an outcome to a comment record in the database """
        with self._session() as conn:
            # tidy up the outcome string to remove quotes which might break the SQL statement
            outcome = outcome.replace('"', '')
            outcome = outcome.replace("'", "")
            sql = '''UPDATE comments SET outcome=? WHERE id=?;'''
            conn.execute(sql, (outcome, comment_id))

    def add_outcome_to_post(self, post_id, outcome):
        """ add an outcome to a post record in the database """

        with self._session() as conn:
            sql = '''UPDATE posts SET outcome=? WHERE id=?;'''
            conn.execute(sql, (outcome, post_id))

    def add_to_posts_list(self, post_id, detox_name_results, detox_body_results, extras, link):
        """ add a post id to the list of previously checked posts """
        with self._session() as conn:
            sql = """INSERT INTO posts(id, name_toxicity, name_non_toxicity, 
            body_toxicity, body_non_toxicity, link, phash) VALUES(?,?,?,?,?,?,?);"""

            conn.execute(sql, (post_id,
                               detox_name_results['toxicity'],
                               detox_name_results['non_toxicity'],
                               detox_body_results['toxicity'] if 'toxicity' in detox_body_results else 0,
                               detox_body_results['non_toxicity'] if 'non_toxicity' in detox_body_results else 1,
                               link,
                               extras['phash'] if 'phash' in extras else None
                               ))

    def add_phash(self, url: str, phash: str):
        with self._session() as conn:
            sql = """INSERT INTO phash(url, phash) VALUES(?,?);"""
            conn.execute(sql, (url, phash))

    def phash_exists(self, phash: str):
        with self._session() as conn:
            sql = """SELECT COUNT(url) FROM phash where phash=?"""
            result = conn.execute(sql, (phash,))
            for row in result.fetchone():
                if row != 0:
                    return True
        return False

    def url_exists(self, url: str) -> Optional[str]:
        with self._session() as conn:
            sql = """SELECT phash FROM phash where url=?"""
            result = conn.execute(sql, (url,))
            for row in result.fetchall():
                if row[0] is not None:
                    return row[0]
        return None

    def get_post_links_by_phash(self, phash: str) -> List[str]:
        with self._session() as conn:
            sql = """SELECT link FROM posts WHERE phash=? LIMIT 5"""
            result = conn.execute(sql, (phash,))
            return [row[0] for row in result.fetchall()]
