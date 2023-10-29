from lemmymodbot import LemmyBot, environment_config
from lemmymodbot import ToxicityProcessor

if __name__ == "__main__":
    bot = LemmyBot([
        ToxicityProcessor(),
    ])
    bot.run()
