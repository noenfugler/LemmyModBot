from pylemmy import Lemmy
from pylemmy.models.post import Post
from pylemmy.models.comment import Comment
from detoxify import Detoxify
import credentials
from datetime import datetime
from time import sleep
from typing import Union
import sqlite3
from pathlib import Path
import os

class Database():
    def __init__(self, directoryname, filename):
        ## a class to handle the databse connection and queries
        self.directoryname = directoryname
        self.filename = filename
        my_directory = Path(self.directoryname)
        if not my_directory.is_dir():
            os.makedirs(self.directoryname)

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

    def add_to_comments_list(self, id):
        # add a comment id to the list of previously checked comments
        conn = sqlite3.connect(self.directoryname + "/" + self.filename)
        # cur = conn.cursor()
        sql = f'INSERT INTO comments(id) VALUES({id})'
        conn.execute(sql)
        conn.commit()
        conn.close()

    def add_to_posts_list(self, id):
        # add a post id to the list of previously checked posts
        conn = sqlite3.connect(self.directoryname + "/" + self.filename)
        sql = f'INSERT INTO posts(id) VALUES({id});'
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
            # print(content)
            if content is not None:
                results = Detoxify('unbiased').predict(content)
                print(results)
                if results['toxicity'] > 0.8:
                    flags.append('toxicity')
                if results['severe_toxicity'] > 0.5:
                    flags.append('severe_toxicity')
                if results['obscene'] > 0.5:
                    flags.append('obscene')
                if results['identity_attack'] > 0.5:
                    flags.append('identity_attack')
                if results['insult'] > 0.8:
                    flags.append('insult')
                if results['threat'] > 0.5:
                    flags.append('threat')
                if results['sexual_explicit'] > 0.8:
                    flags.append('sexual_explicit')
            if len(flags) > 0:
                #we found something bad
                print('***')
                print('REPORT FOR COMMENT:')
                print(flags)
                print('***\n')
                myfile = open("reports.txt", "a")
                try:
                    elem.create_report(reason='Detoxify bot. '+', '.join(flags))
                    print('****************\nREPORTED COMMENT\n******************')
                    myfile.write(str(elem.post_view.post.id) + ", " + name + ", "+content[:50]+", " + '|'.join(flags)+", REPORTED COMMENT\n")
                except:
                    print("ERROR: UNABLE TO CREATE REPORT")
                    myfile.write(str(elem.post_view.post.id) + ", " + name + ", " + content[:50] + ", " + '|'.join(flags) + ", FAILED TO REPORT COMMENT\n")
                myfile.close
            db.add_to_comments_list(id)
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
                results = Detoxify('unbiased').predict(name)
                print(results)
                if results['toxicity'] > 0.8:
                    flags.append('toxicity')
                if results['severe_toxicity'] > 0.5:
                    flags.append('severe_toxicity')
                if results['obscene'] > 0.5:
                    flags.append('obscene')
                if results['identity_attack'] > 0.5:
                    flags.append('identity_attack')
                if results['insult'] > 0.8:
                    flags.append('insult')
                if results['threat'] > 0.5:
                    flags.append('threat')
                if results['sexual_explicit'] > 0.8:
                    flags.append('sexual_explicit')
            if body is not None:
                results = Detoxify('unbiased').predict(body)
                print(results)
                if results['toxicity'] > 0.8:
                    flags.append('toxicity')
                if results['severe_toxicity'] > 0.5:
                    flags.append('severe_toxicity')
                if results['obscene'] > 0.5:
                    flags.append('obscene')
                if results['identity_attack'] > 0.5:
                    flags.append('identity_attack')
                if results['insult'] > 0.8:
                    flags.append('insult')
                if results['threat'] > 0.5:
                    flags.append('threat')
                if results['sexual_explicit'] > 0.8:
                    flags.append('sexual_explicit')
            if len(flags) > 0:
                print('***')
                print('REPORT FOR COMMENT:')
                print(flags)
                print('***\n')
                myfile = open("reports.txt", "a")
                # try:
                if True:
                    elem.create_report(reason='Detoxify bot: '+', '.join(flags))
                    print('****************\nREPORTED POST\n******************')
                    myfile.write(str(elem.post_view.post.id) + ", " + name + ", , " + '|'.join(flags)+", REPORTED POST\n")
                # except:
                else:
                    print("ERROR: UNABLE TO CREATE REPORT")
                    myfile.write(str(elem.post_view.post.id) + ", " + name + ", , " + '|'.join(flags) + ", FAILED TO REPORT POST\n")
                myfile.close
            db.add_to_posts_list(id)
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
    # try:
    multi_stream = lemmy.multi_communities_stream(credentials.communities)
    try:
        multi_stream.content_apply(process_content)
    except:
        print('Error in connection or stream.  Waiting 60s and trying again')
        sleep(60)
