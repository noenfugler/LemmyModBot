# Rename this file to credentials.py and update the values below.
username = "username here"
password = "password here"
instance = "https://lemmy.ml"
communities = ["my_community1", "my_community2", "my_community3"] #communities for the bot to monitor
question_communities = ["my_community2", "my_community3"] # A subset of communities that must have a question mark in the title or body of the post
alt_username = 'username for real user who manages the bot.'
user_watch_list = ["https://lemmy.world/u/user1@instance1.com", "https://lemmy.world/u/user2@instance2.com"]
debug_mode = False  # Setting this value to true will mean that the bot will not actually submit reports.

# The bot basically works on a balance of probabilities approach when deciding whether to report
# content as toxic.  The following parameter increases the threshold of certainty that
# the bot requires before reporting content.  0 = balance of probabilities.  1.0 = never report.
uncertainty_allowance = 0.2


# Matrix login details for the bot to communicate with a Matrix room
"""    
    server : string - The name of the server.  e.g. "https://matrix.example.org"
    account : string - The name of the account e.g. "@alice:example.org"
    password : string - The password for the account e.g. "my-secret-password"
    room_id : string - The id of the room e.g. "!my-fave-room:example.org"
    content : string - The content of the message e.g. "Hello World!"
"""
matrix_server="https://matrix.example.org"
matrix_account="@alice:example.org"
matrix_password="my-secret-password"
matrix_room_id="!my-fave-room:example.org"


