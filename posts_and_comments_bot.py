from pylemmy import Lemmy
from pylemmy.models.post import Post
from pylemmy.models.comment import Comment
from detoxify import Detoxify
import credentials
from datetime import datetime
from typing import Union
import sqlite3
from pathlib import Path
import os
from time import sleep
import traceback

class Database():
    def __init__(self, directoryname, filename):
        ## a class to handle the databse connection and queries
        self.directoryname = directoryname
        self.filename = filename
        my_directory = Path(self.directoryname)
        if not my_directory.is_dir():
            os.makedirs(self.directoryname)
        conn = sqlite3.connect(self.directoryname + "/" + self.filename)
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comments';")
        try:
            for row in result.fetchone():
                pass
        except:
            sql = '''CREATE TABLE "comments" (
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
            result = conn.execute(sql)
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts';")
        try:
            for row in result.fetchone():
                pass
        except:
            sql = '''CREATE TABLE "posts" (
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
            result = conn.execute(sql)

    def in_comments_list(self,id):
        #check whether this comment (id) is stored in the database as having been previously checked
        conn = sqlite3.connect(self.directoryname + "/" + self.filename)
        found = False
        result = conn.execute(f'SELECT count(id) FROM comments WHERE id={id};')
        for row in result.fetchone():
            if row!= 0:
                found = True
        conn.close()
        return found

    def in_posts_list(self, id):
        #check whether this post (id) is stored in the database as having been previously checked
        conn = sqlite3.connect(self.directoryname + "/" + self.filename)
        found = False
        result = conn.execute(f'SELECT count(id) FROM posts WHERE id={id};')
        for row in result.fetchone():
            if row!= 0:
                found = True
        conn.close()
        return found

    def add_to_comments_list(self, id, results):
        # add a comment id to the list of previously checked comments
        conn = sqlite3.connect(self.directoryname + "/" + self.filename)
        # cur = conn.cursor()
        # sql = f'INSERT INTO comments(id) VALUES({id})'
        sql = f'''INSERT INTO comments(id, toxicity, severe_toxicity, obscene, identity_attack, 
        insult, threat, sexual_explicit) VALUES{id, results['toxicity'], 
        results['severe_toxicity'], results['obscene'], results['identity_attack'], 
        results['insult'], results['threat'], results['sexual_explicit']};'''
        # try:
        conn.execute(sql)
        conn.commit()
        conn.close()

    def add_outcome_to_comment(self, id, outcome):
        # add an outcome to a comment
        conn = sqlite3.connect(self.directoryname + "/" + self.filename)
        # tidy up the outcome string to remove quotes which might break the SQL statement
        outcome = outcome.replace('"', '')
        outcome = outcome.replace("'", "")
        sql = f'''UPDATE comments SET outcome='{outcome}' WHERE id={id};'''
        conn.execute(sql)
        conn.commit()
        conn.close()

    def add_outcome_to_post(self, id, outcome):
        # add an outcome to a post
        conn = sqlite3.connect(self.directoryname + "/" + self.filename)
        # cur = conn.cursor()
        # sql = f'INSERT INTO comments(id) VALUES({id})'
        sql = f'''UPDATE posts SET outcome='{outcome}' WHERE id={id};'''
        conn.execute(sql)
        conn.commit()
        conn.close()


    def add_to_posts_list(self, id, name_results, body_results):
        # add a post id to the list of previously checked posts
        conn = sqlite3.connect(self.directoryname + "/" + self.filename)
        sql = f"""INSERT INTO posts(id, name_toxicity, name_severe_toxicity, name_obscene, name_identity_attack, 
        name_insult, name_threat, name_sexual_explicit, body_toxicity, body_severe_toxicity, body_obscene, 
        body_identity_attack, body_insult, body_threat, body_sexual_explicit) VALUES{id, name_results['toxicity'], 
        name_results['severe_toxicity'], name_results['obscene'], name_results['identity_attack'], 
        name_results['insult'], name_results['threat'], name_results['sexual_explicit'], body_results['toxicity'], 
        body_results['severe_toxicity'], body_results['obscene'], body_results['identity_attack'], 
        body_results['insult'], body_results['threat'], body_results['sexual_explicit']};"""

        conn.execute(sql)
        conn.commit()
        conn.close()


def process_content(elem: Union[Post, Comment]):
    # the main doing function, called when a new post or comment is received
    global db
    if isinstance(elem, Comment):
        # It's a comment!
        print('\nCOMMENT:',elem.comment_view.comment.content)
        id=elem.comment_view.comment.id
        if not db.in_comments_list(id):
            flags = []
            content = elem.comment_view.comment.content
            name = elem.comment_view.post.name
            print(datetime.now().isoformat())
            if content is not None:
                results = Detoxify('unbiased').predict(content)
                print(results)
                total = results['toxicity'] + results['severe_toxicity'] + results['obscene'] + results['identity_attack'] + results['insult'] + results['threat'] + results['sexual_explicit']
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
            db.add_to_comments_list(id, results)
            if len(flags) > 0:
                #we found something bad
                print('***')
                print('REPORT FOR COMMENT:')
                print(flags)
                print('***\n')
                try:
                    elem.create_report(reason='Detoxify bot: '+', '.join(flags))
                    print('****************\nREPORTED COMMENT\n******************')
                    db.add_outcome_to_comment(id, "Reported comment for: " + '|'.join(flags))
                except Exception as e:
                    print(e)
                    print("ERROR: UNABLE TO CREATE REPORT")
                    db.add_outcome_to_comment(id, "Failed to report comment for: " + '|'.join(flags)+" due to exception :" + traceback.format_exc())
            else:
                db.add_outcome_to_comment(id, "No report")
        else:
            print('Already Assessed')
    elif isinstance(elem, Post):
        # It's a post
        print('\nPOST:',elem.post_view.post.name)
        id = elem.post_view.post.id
        if not db.in_posts_list(id):
            flags = []
            name = elem.post_view.post.name
            body = elem.post_view.post.body
            print(datetime.now().isoformat())
            if name is not None:
                name_results = Detoxify('unbiased').predict(name)
                print(name_results)
                total = name_results['toxicity'] + name_results['severe_toxicity'] + name_results['obscene'] + name_results['identity_attack'] + name_results['insult'] + name_results['threat'] + name_results['sexual_explicit']
                print(total)
                if name_results['toxicity'] > credentials.toxicity and total > credentials.total:
                    flags.append('toxicity')
                if name_results['severe_toxicity'] > credentials.severe_toxicity and total > credentials.total:
                    flags.append('severe_toxicity')
                if name_results['obscene'] > credentials.obscene and total > credentials.total:
                    flags.append('obscene')
                if name_results['identity_attack'] > credentials.identity_attack and total > credentials.total:
                    flags.append('identity_attack')
                if name_results['insult'] > credentials.insult and total > credentials.total:
                    flags.append('insult')
                if name_results['threat'] > credentials.threat and total > credentials.total:
                    flags.append('threat')
                if name_results['sexual_explicit'] > credentials.sexually_explicit and total > credentials.total:
                    flags.append('sexual_explicit')
            if body is not None:
                body_results = Detoxify('unbiased').predict(body)
                print(body_results)
                total = body_results['toxicity'] + body_results['severe_toxicity'] + body_results['obscene'] + body_results['identity_attack'] + body_results['insult'] + body_results['threat'] + body_results['sexual_explicit']
                print(total)
                if body_results['toxicity'] > credentials.toxicity and total > credentials.total:
                    flags.append('toxicity')
                if body_results['severe_toxicity'] > credentials.severe_toxicity and total > credentials.total:
                    flags.append('severe_toxicity')
                if body_results['obscene'] > credentials.obscene and total > credentials.total:
                    flags.append('obscene')
                if body_results['identity_attack'] > credentials.identity_attack and total > credentials.total:
                    flags.append('identity_attack')
                if body_results['insult'] > credentials.insult and total > credentials.total:
                    flags.append('insult')
                if body_results['threat'] > credentials.threat and total > credentials.total:
                    flags.append('threat')
                if body_results['sexual_explicit'] > credentials.sexually_explicit and total > credentials.total:
                    flags.append('sexual_explicit')
                db.add_to_posts_list(id, name_results, body_results)
            else:
                body_results = {}
                body_results["toxicity"] = 0.0
                body_results["severe_toxicity"] = 0.0
                body_results["obscene"] = 0.0
                body_results["identity_attack"] = 0.0
                body_results["insult"] = 0.0
                body_results["threat"] = 0.0
                body_results["sexual_explicit"] = 0.0
                db.add_to_posts_list(id, name_results, body_results)
            if len(flags) > 0:
                print('***')
                print('REPORT FOR COMMENT:')
                print(flags)
                print('***\n')
                try:
                    post_report = elem.create_report(reason='Detoxify bot: '+', '.join(flags))
                    print('****************\nREPORTED POST\n******************')
                    ##TODO: depending on outcome of error handling changes to pylemmy, may need to add some further/alternate post error handling code here.
                    if not 'error' in post_report.report_view:
                        db.add_outcome_to_post(id, "Reported Post for: " + '|'.join(flags))
                    else:
                        raise "Error when reporting post."
                except Exception as e:
                    print(e)
                    print("ERROR: UNABLE TO CREATE REPORT")
                    db.add_outcome_to_comment(id, "Failed to report post for: " + '|'.join(flags) + " due to exception :" + traceback.format_exc())
                pass
            else:
                db.add_outcome_to_post(id, "No report")

        else:
            print('Already Assessed')

lemmy = Lemmy(
    lemmy_url=credentials.instance,
    username=credentials.username,
    password=credentials.password,
    user_agent="custom user agent (by "+credentials.alt_username+")",
)

while True:
    directoryname = 'history'
    filename = 'history.db'
    db = Database(directoryname, filename)
    multi_stream = lemmy.multi_communities_stream(credentials.communities)
    try:
        multi_stream.content_apply(process_content)
    except:
        print('Error in connection or stream.  Waiting 60s and trying again')
        sleep(60)
