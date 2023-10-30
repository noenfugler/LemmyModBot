from lemmymodbot import LemmyBot
from lemmymodbot import ToxicityProcessor

if __name__ == "__main__":
    bot = LemmyBot([
        ToxicityProcessor(),
    ])
    bot.run()
