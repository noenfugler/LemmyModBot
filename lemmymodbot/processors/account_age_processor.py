from datetime import timedelta

from format_duration import format_duration

from lemmymodbot.processors import Processor, Content, LemmyHandle, ContentResult, ContentType


class AccountAgeProcessor(Processor):
    # Minimum account age in seconds
    minimum_age: int

    def __init__(self, minimum_age: int) -> None:
        self.minimum_age = minimum_age

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        if content.type != ContentType.POST_TITLE and content.type != ContentType.COMMENT:
            return ContentResult.nothing()

        if handle.get_account_details().age >= self.minimum_age:
            return ContentResult.nothing()

        duration = format_duration(timedelta(seconds=self.minimum_age), False)
        handle.post_comment(f"Your account is under the minimum age required by this community ({duration})")
        handle.remove_thing("Account under minimum age")
        return ContentResult.nothing()
