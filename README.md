# LemmyModBot
[![Build](https://github.com/BenMMcLean/LemmyModBot/actions/workflows/build.yml/badge.svg)](https://github.com/BenMMcLean/LemmyModBot/actions/workflows/build.yml) [![Unit Test](https://github.com/BenMMcLean/LemmyModBot/actions/workflows/test.yml/badge.svg)](https://github.com/BenMMcLean/LemmyModBot/actions/workflows/test.yml)

A Lemmy bot written in Python that allows you to automatically moderate communities from toxicity, duplicate posts, and CSAM content.  

This bot is a work in progress and is expected to expand and grow.

## Running the bot
A Docker image is provided for the purposes of easily running the moderation bot in a containerised
environment. To run a bot with just the toxicity detection an example `docker-compose` file has been [provided](docker-compose.example.yml).
To set up further modules (as detailed further below), mount a replacement `main.py` file at `/app/main.py`.

The bot can also be run un-containerised, either by cloning the repo, or by (in the future) using the pip package.

## Modules
Different aspects of moderation are divided into "Processors". These scan and report content for a single kind of 
violation, and can be configured individually. Currently, there are eight different processors:
* **BlacklistProcessor** - This processor allows moderators to provide a list of blacklisted words. If they are encountered in any comment or post, a report is generated.
* **MimeWhitelistProcessor** - This processor whitelists MIME-types of files that are permitted in the community. If a comment or post where this doesn't hold is encountered, a report is generated.
* **MimeBlacklistProcessor** - Same as the previously discussed whitelist, except a blacklist
* **PhashProcessor** - Calculates and tracks a perceptual hash (phash) for each post. If the image has been uploaded before, the bot posts a comment linking to the duplicates.
* **TitleConformityProcessor** - Enforces a certain title structure (specified using Regex) and warns a poster if their title does not match.
* **UserProcessor** - Automatically reports content posted by a listed user.
* **ToxicityProcessor** - Assesses the toxicity of any post/comment and automatically files a report if it is above a specified threshold.
* **PhotoDNAProcessor** *(untested)* - Given a [Microsoft PhotoDNA API Key](https://www.microsoft.com/en-us/photodna), this processor checks posts for Child Sexual Abuse Material (CSAM). If any violating content is found, the post is automatically deleted. Reports of this nature are sent to the provided Matrix server. This processor is untested as I am unable to obtain an API key.
 
