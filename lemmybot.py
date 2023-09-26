""" This file creates and manages a bot to help Moderate one or more Lemmy communities."""

import traceback
from time import sleep
import os
from typing import Union
import logging
import sys
import re
from pprint import pprint
import torch
import numpy as np
import torchtext
import pandas as pd

from pylemmy import Lemmy
from pylemmy.models.post import Post
from pylemmy.models.comment import Comment
from matrix_client.client import MatrixClient

import credentials
from bag_of_words import BagOfWords, build_bow_model
from reconnection_manager import ReconnectionDelayManager
from database import Database


class LemmyBot:
    """ LemmyBot is a bot that checks Lemmy posts and comments for toxicity, as well as
    performing regexp matching, user watchlist monitoring amongst other things."""

    def __init__(self, train_filename="training/train.tsv", rebuild_model=True):

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
            user_agent="custom user agent (by " + credentials.owner_username + ")",
        )
        db_directory_name = 'data'
        db_file_name = 'history.db'
        self.history_db = Database(db_directory_name, db_file_name)

        self.vocab_size = len(self.vocab)
        self.model = BagOfWords(vocab_size=self.vocab_size)
        self.model.load_state_dict(torch.load("data/model.mdl"))
        self.model.eval()

        self.logger.info("Bot starting!")

        self.mydelay = ReconnectionDelayManager(logger=self.logger)

    def build_model(self):
        """ Call to the function to recreate the  model from the training data"""
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
                "osascript -e 'Tell application " + '"System Events" to display dialog "'
                + body + '" with title "' + title + '"' + "'")
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

        # Send a message synchronously.  Returns a result if needed later
        room.send_text(text=m_content)

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
            preds2 = (1 - torch.argmax(preds, dim=-1)).item()
            preds3 = abs(preds[0].item() - preds[1].item())

            print('\n\n' + content)
            print(f'{preds}', (1 - torch.argmax(preds)).item())
            if preds[0].item() < 0.2 and preds[1].item() < 0.2:
                print("Low values^")
                self.messagebox(title="Low Values^", body=content + '\n' + str(preds))
            if abs(preds[0].item() - preds[1].item()) < credentials.uncertainty_allowance:
                print("Close values^")
                self.messagebox(title="Close Values^", body=content + '\n' + str(preds))
            if preds2 == 1 and preds3 >= credentials.uncertainty_allowance:
                sleep(15)
                print("Toxic^")
                self.messagebox(title="Toxic Content", body=content + '\n' + str(preds))
                local_flags.append('potentially toxic')

            return {"toxicity": preds[0].item(),
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
        if not self.history_db.in_comments_list(comment_id):
            flags = []
            content = elem.comment_view.comment.content
            actor_id = elem.comment_view.creator.actor_id

            # Detoxify

            # results = assess_content_toxicity(content)
            comment_results, returned_flags = self.assess_content_toxicity_bow(content)
            flags = flags + returned_flags
            # Actor watch list
            if actor_id in credentials.user_watch_list:
                flags.append('user_watch_list')

            # Regexp
            # Nothing here yet

            # Take action.
            self.history_db.add_to_comments_list(comment_id, comment_results)
            pprint(vars(elem))
            if len(flags) > 0:
                # we found something bad
                self.logger.info('REPORT FOR COMMENT: %s', flags)
                try:
                    if not credentials.debug_mode:
                        elem.create_report(reason='Mod bot (with L plates) : ' + ', '.join(flags))
                    self.logger.info('****************\nREPORTED COMMENT\n******************')
                    self.history_db.add_outcome_to_comment(comment_id, "Reported comment for: "
                                                           + '|'.join(flags))
                except:
                    self.logger.error("ERROR: UNABLE TO CREATE REPORT", exc_info=True)
                    self.history_db.add_outcome_to_comment(comment_id, "Failed to report comment for: "
                                                           + '|'.join(flags) + " due to exception :"
                                                           + traceback.format_exc())
                matrix_message = '\n\nMod bot (with L plates) : ' + ', '.join(flags)
                matrix_message = matrix_message + '\n' + str(comment_results)
                matrix_message = matrix_message + '\n' + str(elem.comment_view.comment)
                self.send_message_to_matrix(m_server=credentials.matrix_server,
                                            m_account=credentials.matrix_account,
                                            m_password=credentials.matrix_password,
                                            m_room_id=credentials.matrix_room_id,
                                            m_content=matrix_message)
            else:
                self.history_db.add_outcome_to_comment(comment_id, "No report")
            sleep(5)
        else:
            self.logger.info('Comment Already Assessed')

    def process_post(self, elem):
        """Determine if the post is new and if so run through detoxifier.  If toxic, then report.
        Update database accordingly"""

        post_id = elem.post_view.post.id
        self.logger.info('POST %s: %s', post_id, elem.post_view.post.name)
        if not self.history_db.in_posts_list(post_id):
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
                    "toxicity": 0.0,
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
            self.history_db.add_to_posts_list(post_id, detox_name_results, detox_body_results)
            if len(flags) > 0:
                self.logger.info('REPORT FOR POST: %s', flags)
                try:
                    if not credentials.debug_mode:
                        elem.create_report(reason='Mod bot (with L plates) : ' + ', '.join(flags))
                    self.logger.info('****************\nREPORTED POST\n******************')
                    self.history_db.add_outcome_to_post(post_id, "Reported Post for: "
                                                        + '|'.join(flags))
                except:
                    self.logger.error("ERROR: UNABLE TO CREATE REPORT", exc_info=True)
                    self.history_db.add_outcome_to_comment(post_id, "Failed to report post for: "
                                                           + '|'.join(flags) + " due to exception :"
                                                           + traceback.format_exc())
                matrix_message = '\n\nMod bot (with L plates) : ' + ', '.join(flags)
                matrix_message = matrix_message + '\n' + str(detox_name_results)
                matrix_message = matrix_message + '\n' + str(detox_body_results)
                matrix_message = matrix_message + '\n' + str(elem.post_view.post)
                self.send_message_to_matrix(m_server=credentials.matrix_server,
                                            m_account=credentials.matrix_account,
                                            m_password=credentials.matrix_password,
                                            m_room_id=credentials.matrix_room_id,
                                            m_content=matrix_message)
            else:
                self.history_db.add_outcome_to_post(post_id, "No report")
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
        # sleep(5)

    def run(self):
        print("Test")
        """This is the main run loop for the bot.  It should be called after initiation of bot"""
        while True:
            try:
                multi_stream = self.lemmy.multi_communities_stream(credentials.communities)
                multi_stream.content_apply(self.process_content)
            except:
                self.logger.error("Exception raised!", exc_info=True)
                self.mydelay.wait()
