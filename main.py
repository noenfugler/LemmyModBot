# This script is a simple bot to test plemmy.
from plemmy import LemmyHttp
import credentials


def print_hi(name):

    # create object for Lemmy.ml
    srv = LemmyHttp("https://lemmy.world")

    # log in to Lemmy.ml
    srv.login(username, password)
    foo = srv.search(community_name="botplayground")
    print(foo)
    # make a comment
    # srv.create_comment("Hello from plemmy!", post_id)

    # create a post
    srv.create_post(community_id, "New post's title", body="Body text", url="https://a.link.to.share")

if __name__ == '__main__':
    print_hi('PyCharm')

