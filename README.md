# LemmyModBot
A Lemmy bot written in Python using [pylemmy](https://github.com/dcferreira/pylemmy) to access comment and create reports.  

This bot is a work in progress and is expected to expand and grow.

## Neural Network accuracy
LemmyModBot can detect and report toxic written content on Lemmy communities using a 512-64-2 bag of words deep text classification Neural Network using Pytorch and a local dataset for training.

The neural network with the supplied training dataset is currently achieving accuracies of around 75-80% in detecting toxic content.  Ongoing addition of ambiguous or misclassified data to the training set is hoped to improve this.

## Example Usage

from lemmybot import LemmyBot

lemmy_world = LemmyBot(rebuild_model=True)
  
lemmy_world.run()
 
