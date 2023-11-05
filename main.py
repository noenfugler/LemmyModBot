from lemmymodbot import LemmyBot, MimeWhitelistProcessor
from lemmymodbot import ToxicityProcessor

if __name__ == "__main__":
    bot = LemmyBot([
        ToxicityProcessor(),
        MimeWhitelistProcessor(
            type_whitelist=["image", "video"]
        )
    ])
    bot.run()
