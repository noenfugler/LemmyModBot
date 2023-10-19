import datetime as dt
from time import sleep


class ReconnectionDelayManager:
    """ This class creates an object to provide escalating wait times when the server times out.
    The first wait should be 30sec, the second should be 60sec, etc up until a maximum of 5min
    between attempts.  If there are no calls to this object within the reset time period (6 mins),
    it resets to the start again."""

    def __init__(self, logger, wait_increment=30, max_count=10, reset_time=360):
        self.count = 1
        self.last_time = dt.datetime.now()

        # each iteration is this much longer
        self.wait_increment = wait_increment

        # Maximum wait in iterations
        self.max_count = max_count

        # reset self.count after going this long without wait being called.
        self.reset_time = reset_time

        self.logger = logger

    def wait(self):
        """This method waits the current delay period and updates the next delay period"""

        if (dt.datetime.now() - self.last_time).total_seconds() > self.reset_time:
            self.count = 1
        wait_time = self.count * self.wait_increment
        self.logger.error(
            f"""Error in connection, stream or process_content.  
            Waiting {wait_time} seconds and trying again"""
        )
        sleep(self.count * self.wait_increment)
        self.count += 1
        if self.count > self.max_count:
            self.count = self.max_count
        self.last_time = dt.datetime.now()

    def reset(self):
        """ Reset the manager"""
        self.count = 1