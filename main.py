from lemmybot import LemmyBot
from processor import ToxicityProcessor, UserProcessor

if __name__ == "__main__":
    bot = LemmyBot([
        ToxicityProcessor(),
        UserProcessor()
    ])
    bot.run()
