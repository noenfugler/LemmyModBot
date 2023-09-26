from time import sleep
from typing import List, Any, Optional

import numpy as np
import pandas as pd
import torch
import torchtext
from pandas import DataFrame
from torch.types import Device
from torchtext.vocab import Vocab
import re

import config
from bag_of_words import BagOfWords, build_bow_model


class ContentType:
    POST_TITLE = 0
    POST_BODY = 1
    COMMENT = 2


class Content:
    community: str
    content: str
    actor_id: str
    type: ContentType

    def __init__(self, community: str, content: str, actor_id: str, type: ContentType):
        self.community = community
        self.content = content
        self.actor_id = actor_id
        self.type = type


class ContentResult:
    flags: List[str]
    extras: Optional[Any]
    comment: Optional[str]

    def __init__(self, flags: List[str], extras: Optional[Any], comment: Optional[str] = None):
        self.flags = flags
        self.extras = extras
        self.comment = comment

    @staticmethod
    def nothing():
        return ContentResult([], None)


class Processor:

    def setup(self) -> None:
        pass

    def execute(self, content: Content) -> ContentResult:
        return ContentResult.nothing()


class ToxicityProcessor(Processor):
    train_filename: str
    rebuild_model: bool
    uncertainty_allowance = 0.2
    device: Device
    tokenizer: Any
    all_data: DataFrame
    vocab: Vocab
    vocab_size: int
    model: BagOfWords

    def __init__(self, train_filename: str = "training/train.tsv", rebuild_model: bool = True):
        self.train_filename = train_filename
        self.rebuild_model = rebuild_model

    def setup(self) -> None:
        if self.rebuild_model:
            build_bow_model()

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

        self.vocab_size = len(self.vocab)
        self.model = BagOfWords(vocab_size=self.vocab_size)
        self.model.load_state_dict(torch.load("data/model.mdl"))
        self.model.eval()

    def execute(self, content: Content) -> ContentResult:
        local_flags = []
        my_tokens = {}
        if content is not None:
            my_tokens['tokens'] = self.tokenizer(content.content)
            my_numericals = {}
            my_numericals['ids'] = self.numericalize_data(my_tokens)
            my_multi_hot = self.multi_hot_data(my_numericals)
            inputs = torch.tensor(my_multi_hot).to(self.device)
            # if inputs.dtype != torch.float64:
            #     inputs = inputs.float()
            preds = self.model(inputs)
            preds2 = (1 - torch.argmax(preds, dim=-1)).item()
            preds3 = abs(preds[0].item() - preds[1].item())

            print('\n\n' + content.content)
            print(f'{preds}', (1 - torch.argmax(preds)).item())
            if preds[0].item() < 0.2 and preds[1].item() < 0.2:
                print("Low values^")
            if abs(preds[0].item() - preds[1].item()) < config.uncertainty_allowance:
                print("Close values^")
            if preds2 == 1 and preds3 >= config.uncertainty_allowance:
                sleep(15)
                print("Toxic^")
                local_flags.append('potentially toxic')

            return ContentResult(local_flags, {
                "toxicity": preds[0].item(),
                "non_toxicity": preds[1].item(),
            })
        else:
            return ContentResult.nothing()

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


class UserProcessor(Processor):
    user_watch_list: List[str]

    def __init__(self, user_watch_list: List[str]):
        self.user_watch_list = user_watch_list

    def execute(self, content: Content) -> ContentResult:
        if content.actor_id in self.user_watch_list:
            return ContentResult(['user_watch_list'], None)
        return ContentResult.nothing()


class BlacklistProcessor(Processor):
    blacklist: List[str]
    tokenizer: Any

    def __init__(self, blacklist: List[str]):
        self.blacklist = blacklist

    def setup(self) -> None:
        self.tokenizer = torchtext.data.utils.get_tokenizer("basic_english")

    def execute(self, content: Content) -> ContentResult:
        tokens = self.tokenizer(content.content.lower())
        if any(x in self.blacklist for x in tokens):
            return ContentResult(['word_blacklist'], None)
        return ContentResult.nothing()


class TitleCommenterProcessor(Processor):
    message: str

    def __init__(self, regex: str, message: str):
        self.pattern = re.compile(regex)
        self.message = message

    def execute(self, content: Content) -> ContentResult:
        if content.type != ContentType.POST_TITLE:
            return ContentResult.nothing()

        if not self.pattern.match(content.content):
            return ContentResult([], None, self.message)

        return ContentResult.nothing()

