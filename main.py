from lemmybot import LemmyBot
from processor import ToxicityProcessor, UserProcessor, BlacklistProcessor

if __name__ == "__main__":
    bot = LemmyBot([
        ToxicityProcessor(),
        UserProcessor(),
        BlacklistProcessor()
    ])
    bot.run()
