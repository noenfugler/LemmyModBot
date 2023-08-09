""" This file creates and manages to bot.
TODO:  Move main content to a separate library"""

import traceback
from time import sleep
import os
from pathlib import Path
import sqlite3
from typing import Union
import logging
import sys
import re
import datetime as dt
import torch
import numpy as np
import torchtext
import pandas as pd
from pprint import pprint

from pylemmy import Lemmy
from pylemmy.models.post import Post
from pylemmy.models.comment import Comment
import credentials
from models.bag_of_words import BagOfWords, build_bow_model


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
        detox_body_results['toxicity'], detox_body_results['non_toxicity'], };"""

        conn.execute(sql)
        conn.commit()
        conn.close()

class ReconnectionDelayManager:
    """ This class creates an object to provide escalating wait times when the server times out.
    The first wait should be 30sec, the second should be 60sec, etc up until a maximum of 5min
    between attempts.  If there are no calls to this object within the reset time period (6 mins),
    it resets to the start again."""
    def __init__(self, logger, wait_increment = 30, max_count = 10, reset_time = 360):
        self.count = 1
        self.last_time = dt.datetime.now()

        # each iteration is this much longer
        self.wait_increment = wait_increment

        # Maximum wait in iterations
        self.max_count = max_count

        # reset self.count after going this long without wait being called.
        self.reset_time = reset_time

        self.logger = logger

    def wait(self):
        """This method waits the current delay period and updates the next delay period"""

        if (dt.datetime.now() - self.last_time).total_seconds() > self.reset_time:
            self.count = 1
        wait_time = self.count*self.wait_increment
        self.logger.error(
            f"""Error in connection, stream or process_content.  
            Waiting {wait_time} seconds and trying again"""
        )
        sleep(self.count*self.wait_increment)
        self.count += 1
        if self.count > self.max_count:
            self.count = self.max_count
        self.last_time = dt.datetime.now()

    def reset(self):
        """ Reset the manager"""
        self.count = 1

class LemmyBot:
    def __init__(self, train_filename="data/train.tsv", rebuild_model = True):

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        if rebuild_model:
            self.build_model()


        self.train_filename = train_filename
        # initialise deep neural network model
        """
        Load the data and set up the tokenizer and dataset for creating/training/using the model.

        :param train_filename: file path and location for the dataset
        :return len(vocab): the length of the vocabulary
        """

        # global tokenizer, vocab, device

        torch.set_default_dtype(torch.float64)

        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

        # load training data for vocab
        self.all_data = pd.read_csv(self.train_filename, sep='\t', lineterminator='\n')

        self.tokenizer = torchtext.data.utils.get_tokenizer("basic_english")
        self.all_data['tokens'] = self.all_data.apply(lambda row: self.tokenizer(row['comment']), axis=1)

        # build a vocabulary
        self.vocab = torchtext.vocab.build_vocab_from_iterator(self.all_data['tokens'],
                                                          min_freq=5,
                                                          specials=['<unk>', '<pad>'])
        self.vocab.set_default_index(self.vocab['<unk>'])
        # return len(self.vocab)

        self.lemmy = Lemmy(
            lemmy_url=credentials.instance,
            username=credentials.username,
            password=credentials.password,
            user_agent="custom user agent (by " + credentials.alt_username + ")",
        )
        DB_DIRECTORY_NAME = 'history'
        DB_FILE_NAME = 'history.db'
        self.db = Database(DB_DIRECTORY_NAME, DB_FILE_NAME)

        self.vocab_size = len(self.vocab)
        self.model = BagOfWords(vocab_size=self.vocab_size)
        self.model.load_state_dict(torch.load("model.mdl"))
        self.model.eval()

        self.logger.info("Bot starting!")

        self.mydelay = ReconnectionDelayManager(logger=self.logger)


    def build_model(self):
        build_bow_model()

    def messagebox(self, title, body):
        """ A simple messagebox call to notify the user"""
        if sys.platform == "darwin":
            # Only works on OS X at this time

            # Remove any quotes that mess up the messagebox call
            title = title.replace('"', '')
            title = title.replace("'", '')
            body = body.replace('"', '')
            body = body.replace("'", '')

            # Create messagebox
            return os.system(
                "osascript -e 'Tell application " + '"System Events" to display dialog "' + body + '" with title "' + title + '"' + "'")
            # osascript -e 'Tell application "System Events" to display dialog "Some Funky Message" with title "Hello Matey"'

    def send_message_to_matrix(self, m_server, m_account, m_password, m_room_id, m_content):
        """ Send a message to a matrix room
        parameters:
        server : string - The name of the server.  e.g. "https://matrix.example.org"
        account : string - The name of the account e.g. "@alice:example.org"
        password : string - The password for the account e.g. "my-secret-password"
        room_id : string - The id of the room e.g. "!my-fave-room:example.org"
        content : string - The content of the message e.g. "Hello World!"
        """

        # Create a Matrix client instance
        client = MatrixClient(m_server)

        # Log in
        # client.login_with_password(username=m_account, password=m_password)
        client.login(username=m_account, password=m_password, sync=True)

        # Get a room instance
        room = client.join_room(m_room_id)

        # Send a message synchronously
        response = room.send_text(text=m_content)

        # Wait for the response before continuing
        # response.wait_for_response()
        client.logout()

    def clean_content(self, content):
        """Tidy up content to remove unwanted characters before processing text"""

        content = content.replace("\n\r", " ")
        content = content.replace("\n", " ")
        content = content.replace("\r", " ")
        content = content.replace("\t", ' ')
        content = content.replace("<br>", " ")
        return content



    def numericalize_data(self, example):
        """ Convert tokens into vocabulary index."""
        ids = [self.vocab[token] for token in example['tokens']]
        return ids

    def multi_hot_data(self, example):
        """ Convert to a mult-hot list for training/assessment"""
        num_classes = len(self.vocab)
        encoded = np.zeros((num_classes,))
        encoded[example['ids']] = 1
        return encoded

    def assess_content_toxicity_bow(self, content):
        """Use the pretrained deep learning model model.mdl to
        classify content as either toxic or not"""

        # global device
        local_flags = []
        my_tokens = {}
        if content is not None:
            content = self.clean_content(content)
            my_tokens['tokens'] = self.tokenizer(content)
            my_numericals = {}
            my_numericals['ids'] = self.numericalize_data(my_tokens)
            my_multi_hot = self.multi_hot_data(my_numericals)
            inputs = torch.tensor(my_multi_hot).to(self.device)
            # if inputs.dtype != torch.float64:
            #     inputs = inputs.float()
            preds = self.model(inputs)
            preds2 = (1-torch.argmax(preds, dim=-1)).item()
            preds3 = abs(preds[0].item() - preds[1].item())

            print('\n\n'+content)
            print(f'{preds}', (1-torch.argmax(preds)).item())
            if preds[0].item() < 0.2 and preds[1].item() < 0.2:
                print("Low values^")
                self.messagebox(title = "Low Values^", body = content + '\n' + str(preds))
            if abs(preds[0].item() - preds[1].item()) < credentials.uncertainty_allowance :
                print("Close values^")
                self.messagebox(title = "Close Values^", body = content + '\n' + str(preds))
            if preds2 == 1 and preds3 >= credentials.uncertainty_allowance:
                sleep(15)
                print("Toxic^")
                self.messagebox(title = "Toxic Content", body = content + '\n' + str(preds))
                local_flags.append('potentially toxic')

            return {"toxicity":preds[0].item(),
                    "non_toxicity": preds[1].item(),
                    }, local_flags
        else:
            return None, None



    def process_comment(self, elem):
        """Determine if the comment is new and if so run through detoxifier.  If toxic, then rrt.
        Update database accordingly"""

        comment_id = elem.comment_view.comment.id
        self.logger.info('COMMENT %s: %s', comment_id, elem.comment_view.comment.content)
        if comment_id == 1313063:
            pass
            # Opportunity for some debugging here
        if not self.db.in_comments_list(comment_id):
            flags = []
            content = elem.comment_view.comment.content
            actor_id = elem.comment_view.creator.actor_id

            # Detoxify

            # results = assess_content_toxicity(content)
            results, returned_flags = self.assess_content_toxicity_bow(content)
            flags = flags + returned_flags
            # Actor watch list
            if actor_id in credentials.user_watch_list:
                flags.append('user_watch_list')

            # Regexp
            # Nothing here yet

            # Take action.
            self.db.add_to_comments_list(comment_id, results)
            pprint(vars(elem))
            if len(flags) > 0:
                # we found something bad
                self.logger.info('REPORT FOR COMMENT: %s', flags)
                try:
                    if not credentials.debug_mode:
                        elem.create_report(reason='Mod bot (with L plates) : ' + ', '.join(flags))
                    self.logger.info('****************\nREPORTED COMMENT\n******************')
                    self.db.add_outcome_to_comment(comment_id, "Reported comment for: " + '|'.join(flags))
                except:
                    self.logger.error("ERROR: UNABLE TO CREATE REPORT", exc_info=True)
                    self.db.add_outcome_to_comment(comment_id, "Failed to report comment for: " + '|'.join(
                        flags) + " due to exception :" + traceback.format_exc())
                self.send_message_to_matrix(m_server=credentials.matrix_server,
                                                   m_account=credentials.matrix_account,
                                                   m_password=credentials.matrix_password,
                                                   m_room_id=credentials.matrix_room_id,
                                                   m_content='\n\nMod bot (with L plates) : ' + ', '.join(flags) + '\n' + str(elem.comment_view.comment))
            else:
                self.db.add_outcome_to_comment(comment_id, "No report")
            sleep(5)
        else:
            self.logger.info('Comment Already Assessed')


    def process_post(self, elem):
        """Determine if the post is new and if so run through detoxifier.  If toxic, then report.
        Update database accordingly"""

        post_id = elem.post_view.post.id
        self.logger.info('POST %s: %s', post_id, elem.post_view.post.name)
        if not self.db.in_posts_list(post_id):
            flags = []
            name = elem.post_view.post.name
            body = elem.post_view.post.body
            community = elem.post_view.community.name
            actor_id = elem.post_view.creator.actor_id

            # Actor in watch list?
            if actor_id in credentials.user_watch_list:
                flags.append('user_watch_list')

            # Detox results
            # detox_name_results = assess_content_toxicity(name)
            # detox_body_results = assess_content_toxicity(body)
            # BoW Results
            detox_name_results, local_flags_name = self.assess_content_toxicity_bow(name)
            if body is not None:
                detox_body_results, local_flags_body = self.assess_content_toxicity_bow(body)
                local_flags = list(set(local_flags_name + local_flags_body))
                flags = flags + local_flags
            else:
                flags = flags + local_flags_name
                detox_body_results = {
                    "toxicity":0.0,
                    "non_toxicity": 0.0
                }
            # Regexp
            if community in credentials.question_communities:
                question_re = re.compile('.*\?')
                regexp_name_result = question_re.match(name)
                if body is not None:
                    regexp_body_result = question_re.match(body)
                else:
                    regexp_body_result = False
                if (not (regexp_name_result or regexp_body_result) \
                        and (community in credentials.question_communities)
                    ):
                    flags.append('No ? mark')
                    print('\n\n*******REGEXP MATCH*******\n')

            # Take action
            self.db.add_to_posts_list(post_id, detox_name_results, detox_body_results)
            if len(flags) > 0:
                self.logger.info('REPORT FOR POST: %s', flags)
                try:
                    if not credentials.debug_mode:
                        elem.create_report(reason='Mod bot (with L plates) : ' + ', '.join(flags))
                    self.logger.info('****************\nREPORTED POST\n******************')
                    self.db.add_outcome_to_post(post_id, "Reported Post for: " + '|'.join(flags))
                except:
                    self.logger.error("ERROR: UNABLE TO CREATE REPORT", exc_info=True)
                    self.db.add_outcome_to_comment(post_id, "Failed to report post for: " + '|'.join(
                        flags) + " due to exception :" + traceback.format_exc())
                self.send_message_to_matrix(m_server=credentials.matrix_server,
                                       m_account=credentials.matrix_account,
                                       m_password=credentials.matrix_password,
                                       m_room_id=credentials.matrix_room_id,
                                       m_content='\n\nMod bot (with L plates) : ' + ', '.join(flags) + '\n' + str(elem.post_view.post))
            else:
                self.db.add_outcome_to_post(post_id, "No report")
            sleep(5)

        else:
            self.logger.info('Post Already Assessed')


    def process_content(self, elem: Union[Post, Comment]):
        """ the main doing function, called when a new post or comment is received"""

        if isinstance(elem, Comment):
            # It's a comment!
            self.process_comment(elem)
        elif isinstance(elem, Post):
            # It's a post
            self.process_post(elem)
        sleep(5)

    def run(self):
        while True:
            try:
                multi_stream = self.lemmy.multi_communities_stream(credentials.communities)
                multi_stream.content_apply(self.process_content)
            except:
                self.logger.error("Exception raised!", exc_info=True)
                self.mydelay.wait()
