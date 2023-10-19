from lemmybot import LemmyBot
from processors import ToxicityProcessor

if __name__ == "__main__":
    bot = LemmyBot([
        ToxicityProcessor()
    ])
    bot.run()
