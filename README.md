# LemmyModBot
A Lemmy bot written in Python to detect and report toxic written content on Lemmy communities.  LemmModBot uses [pylemmy](https://github.com/dcferreira/pylemmy) to access comment and create reports.  Text classification is done using a 512-64-2 bag of words Deep NN using Pytorch.

Local Dataset is used for training and TODO: will be updated by mod decisions.

This bot is a work in progress and is expected to expand and grow.

## Nerual Network accuracy
The neural network with the supplied training dataset is currently achieving accuracies of around 75-80% in detecting toxic content.

## Example Usage

  from lemmybot import LemmyBot

  lemmy_world = LemmyBot(rebuild_model=True)
  
  lemmy_world.run()
 
