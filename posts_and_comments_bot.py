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

from pylemmy import Lemmy
from pylemmy.models.post import Post
from pylemmy.models.comment import Comment
from detoxify import Detoxify
import credentials
from models import BoW
import torch
import numpy as np
import torchtext
import pandas as pd
# import pyautogui
# from CTkMessagebox import CTkMessagebox

import Bow2

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def clean_content(content):
    content = content.replace("\n\r", " ")
    content = content.replace("\n", " ")
    content = content.replace("\r", " ")
    content = content.replace("\t", ' ')
    content = content.replace("<br>", " ")
    # content = content.replace('"', '~')
    # content = content.replace("'", '~')
    return content

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

    def add_to_posts_list(self, post_id, detox_name_results, detox_body_results):
        """ add a post id to the list of previously checked posts """

        conn = sqlite3.connect(self.db_location)
        sql = f"""INSERT INTO posts(id, name_toxicity, name_severe_toxicity, name_obscene, 
        name_identity_attack, name_insult, name_threat, name_sexual_explicit, body_toxicity, 
        body_severe_toxicity, body_obscene, body_identity_attack, body_insult, body_threat, 
        body_sexual_explicit) VALUES{post_id, detox_name_results['toxicity'], 
        detox_name_results['severe_toxicity'], detox_name_results['obscene'], detox_name_results['identity_attack'],
        detox_name_results['insult'], detox_name_results['threat'], detox_name_results['sexual_explicit'], 
        detox_body_results['toxicity'], detox_body_results['severe_toxicity'], detox_body_results['obscene'], 
        detox_body_results['identity_attack'], detox_body_results['insult'], detox_body_results['threat'], 
        detox_body_results['sexual_explicit']};"""

        conn.execute(sql)
        conn.commit()
        conn.close()

def initialise_bow(filename="data/train.tsv"):
    # train_dataset_dict = load_dataset('text', data_files='data/train.tsv')
    global tokenizer, vocab
    global device

    torch.set_default_dtype(torch.float64)

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

    all_data = pd.read_csv(filename, sep='\t', lineterminator='\n')
    # train_data

    tokenizer = torchtext.data.utils.get_tokenizer("basic_english")
    max_length = 600
    all_data['tokens'] = all_data.apply(lambda row: tokenizer(row['comment']), axis=1)

    # build a vocabulary
    vocab = torchtext.vocab.build_vocab_from_iterator(all_data['tokens'],
                                                      min_freq=5,
                                                      specials=['<unk>', '<pad>'])
    vocab.set_default_index(vocab['<unk>'])
    return len(vocab)

def numericalize_data(example, vocab):
    ids = [vocab[token] for token in example['tokens']]
    return ids

def multi_hot_data(example, num_classes):
    encoded = np.zeros((num_classes,))
    encoded[example['ids']] = 1
    return encoded



def assess_content_toxicity_bow(content):
    global TP, FP, TN, FN
    global tokenizer
    local_flags = []
    my_tokens = {}
    if content is not None:
        content = clean_content(content)
        my_tokens['tokens'] = tokenizer(content)
        my_numericals = {}
        my_numericals['ids'] = numericalize_data(my_tokens, vocab)
        my_multi_hot = multi_hot_data(my_numericals, len(vocab))
        inputs = torch.tensor(my_multi_hot).to(device)
        # if inputs.dtype != torch.float64:
        #     inputs = inputs.float()
        preds = model(inputs)
        preds2 = (1-torch.argmax(preds, dim=-1)).item()

        # if preds2 == 1:
        #     local_flags.append('toxic')
        print('\n\n'+content)
        print(f'{preds}', (1-torch.argmax(preds)).item())
        # is_toxic = input("[T]oxic, [S]kip, [N]ot toxic : ")
        # is_toxic = CTkMessagebox(title="Toxic?", message=content + str(preds.item()),
        #                     icon="warning", option_1="Toxic", option_2="Skip", option_3="Not toxic")
        # with open("data/train.tsv", "a") as myfile:
        if preds2 == 1:
            sleep(15)
            # print("Toxic")
            # myfile.write("\n" + content + '\t"{""toxic_content"":true}"')
            local_flags.append('toxic')
            # if preds2 == 1:
            # TP += 1
            # else:
            #     FN += 1
        # elif is_toxic.upper() == "N":
        # else:
            # print("Not toxic")
            # myfile.write("\n" + content + '\t"{""toxic_content"":false}"')
            # if preds2 == 1:
            #     FP += 1
            # else:
            #     TN += 1
        # else:
        #     print("Skipping")
        # print("TP, FP", TP, FP)
        # print("FN, TN", FN, TN)
        # myfile.close()
        return {"toxicity":(preds[0]-preds[1]).item(), "severe_toxicity": 0.0, "obscene": 0.0, "identity_attack": 0.0, "insult":0.0, "sexual_explicit":0.0, "threat": 0.0}, local_flags
    else:
        return None, None
    sleep(5)

def assess_content_toxicity(content):
    """Process content using Detoxify and return results as a dictionary"""
    # flags = []
    global flags

    if content is not None:
        results = Detoxify('unbiased').predict(content)
        logger.info("Detoxify results: %s", results)
        total = results['toxicity'] + \
            results['severe_toxicity'] + \
            results['obscene'] + \
            results['identity_attack'] + \
            results['insult'] + \
            results['threat'] + \
            results['sexual_explicit']
        logger.info("Content toxicity assessment total: %s", total)
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
    """Determine if the comment is new and if so run through detoxifier.  If toxic, then rrt.
    Update database accordingly"""

    comment_id = elem.comment_view.comment.id
    logger.info('COMMENT %s: %s', comment_id, elem.comment_view.comment.content)
    if comment_id == 1313063:
        pass
        # Opportunity for some debugging here
    if not db.in_comments_list(comment_id):
        flags = []
        content = elem.comment_view.comment.content
        actor_id = elem.comment_view.creator.actor_id

        # Detoxify

        # results = assess_content_toxicity(content)
        results, returned_flags = assess_content_toxicity_bow(content)
        flags = flags + returned_flags
        # Actor watch list
        if actor_id in credentials.user_watch_list:
            flags.append('user_watch_list')

        # Regexp
        # Nothing here yet

        # Take action.
        db.add_to_comments_list(comment_id, results)
        if len(flags) > 0:
            # we found something bad
            logger.info('REPORT FOR COMMENT: %s', flags)
            try:
                elem.create_report(reason='Mod bot: ' + ', '.join(flags))
                logger.info('****************\nREPORTED COMMENT\n******************')
                db.add_outcome_to_comment(comment_id, "Reported comment for: " + '|'.join(flags))
            except:
                logger.error("ERROR: UNABLE TO CREATE REPORT", exc_info=True)
                db.add_outcome_to_comment(comment_id, "Failed to report comment for: " + '|'.join(
                    flags) + " due to exception :" + traceback.format_exc())
        else:
            db.add_outcome_to_comment(comment_id, "No report")
            pass
        sleep(5)
    else:
        logger.info('Comment Already Assessed')


def process_post(elem):
    """Determine if the post is new and if so run through detoxifier.  If toxic, then report.
    Update database accordingly"""

    post_id = elem.post_view.post.id
    logger.info('POST %s: %s', post_id, elem.post_view.post.name)
    if post_id == 638082:
        pass
    if not db.in_posts_list(post_id):
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
        detox_name_results, local_flags_name = assess_content_toxicity_bow(name)
        if body is not None:
            detox_body_results, local_flags_body = assess_content_toxicity_bow(body)
            local_flags = list(set(local_flags_name + local_flags_body))
            flags = flags + local_flags
        else:
            flags = flags + local_flags_name
            detox_body_results = {"toxicity":0.0, "severe_toxicity": 0.0, "obscene": 0.0, "identity_attack": 0.0, "insult":0.0, "sexual_explicit":0.0, "threat": 0.0}
        # Regexp
        if community in credentials.question_communities:
            question_re = re.compile('.*\?$')
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
        db.add_to_posts_list(post_id, detox_name_results, detox_body_results)
        if len(flags) > 0:
            logger.info('REPORT FOR POST: %s', flags)
            try:
                elem.create_report(reason='Mod bot: ' + ', '.join(flags))
                logger.info('****************\nREPORTED POST\n******************')
                db.add_outcome_to_post(post_id, "Reported Post for: " + '|'.join(flags))
            except:
                logger.error("ERROR: UNABLE TO CREATE REPORT", exc_info=True)
                db.add_outcome_to_comment(post_id, "Failed to report post for: " + '|'.join(
                    flags) + " due to exception :" + traceback.format_exc())
        else:
            db.add_outcome_to_post(post_id, "No report")
            pass
        sleep(5)

    else:
        logger.info('Post Already Assessed')


def process_content(elem: Union[Post, Comment]):
    """ the main doing function, called when a new post or comment is received"""

    if isinstance(elem, Comment):
        # It's a comment!
        process_comment(elem)
    elif isinstance(elem, Post):
        # It's a post
        process_post(elem)

class DelayManager:
    """ This class creates an object to provide escalating wait times when the server times out.
    The first wait should be 30sec, the second should be 60sec, etc up until a maximum of 5min between
    attempts.  If there are no calls to this object within the reset time period (6 mins), it resets to
    the start again."""
    def __init__(self):
        self.count = 1
        self.last_time = dt.datetime.now()
        self.wait_increment = 30    # each iteration is this much longer
        self.max_count = 10         # Maximum wait in iterations
        self.reset_time = 360       # reset self.count after going this long without wait being called.

    def wait(self):
        if (dt.datetime.now() - self.last_time).total_seconds() > self.reset_time:
            self.count = 1
        logger.error(
            f'Error in connection, stream or process_content.  Waiting {self.count*self.wait_increment} seconds and trying again'
        )
        sleep(self.count*self.wait_increment)
        self.count += 1
        if self.count > self.max_count:
            self.count = self.max_count
        self.last_time = dt.datetime.now()

if __name__ == '__main__':
    lemmy = Lemmy(
        lemmy_url=credentials.instance,
        username=credentials.username,
        password=credentials.password,
        user_agent="custom user agent (by " + credentials.alt_username + ")",
    )
    DB_DIRECTORY_NAME = 'history'
    DB_FILE_NAME = 'history.db'
    db = Database(DB_DIRECTORY_NAME, DB_FILE_NAME)

    vocab_size = initialise_bow()
    model = BoW(vocab_size=vocab_size)
    model.load_state_dict(torch.load("model.mdl"))
    model.eval()

    logger.info("Bot starting!")

    TP = 0
    FP = 0
    TN = 0
    FN = 0

    mydelay = DelayManager()

    while True:
        try:
            multi_stream = lemmy.multi_communities_stream(credentials.communities)
            multi_stream.content_apply(process_content)
        except:
            logger.error("Exception raised!", exc_info=True)
            mydelay.wait()
