from pathlib import Path
import sqlite3


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
        sql = f'''INSERT INTO comments(id, toxicity, non_toxicity) VALUES{comment_id,
        results['toxicity'], results['non_toxicity']};'''
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

    def add_to_posts_list(self, post_id, detox_name_results, detox_body_results):
        """ add a post id to the list of previously checked posts """

        conn = sqlite3.connect(self.db_location)
        sql = f"""INSERT INTO posts(id, name_toxicity, name_non_toxicity, 
        body_toxicity, body_non_toxicity) VALUES{post_id,
        detox_name_results['toxicity'], detox_name_results['non_toxicity'],
        detox_body_results['toxicity'], detox_body_results['non_toxicity'],};"""

        conn.execute(sql)
        conn.commit()
        conn.close()