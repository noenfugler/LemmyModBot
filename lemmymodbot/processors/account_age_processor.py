from datetime import timedelta

from format_duration import format_duration

from lemmymodbot.processors import Processor, Content, LemmyHandle, ContentResult


class AccountAgeProcessor(Processor):
    # Minimum account age in seconds
    minimum_age: int

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        if handle.get_account_details().age >= self.minimum_age:
            return ContentResult.nothing()

        duration = format_duration(timedelta(seconds=self.minimum_age), False)
        handle.post_comment(f"Your account is under the minimum age required by this community ({duration})")
        handle.remove_thing("Account under minimum age")
        return ContentResult.nothing()