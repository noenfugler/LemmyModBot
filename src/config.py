# Rename this file to config.py and update the values below.
import os

username = os.getenv("LEMMY_USERNAME")
password = os.getenv("LEMMY_PASSWORD")
instance = os.getenv("LEMMY_INSTANCE")
owner_username = os.getenv("LEMMY_OWNER_USERNAME")
communities = [x.strip() for x in os.getenv("LEMMY_COMMUNITIES").split(',')]
debug_mode = False  # Setting this value to true will mean that the bot will not actually submit reports.

# Matrix login details for the bot to communicate with a Matrix room
"""    
    server : string - The name of the server.  e.g. "https://matrix.example.org"
    account : string - The name of the account e.g. "@alice:example.org"
    password : string - The password for the account e.g. "my-secret-password"
    room_id : string - The id of the room e.g. "!my-fave-room:example.org"
    content : string - The content of the message e.g. "Hello World!"
"""
matrix_server = os.getenv("MATRIX_INSTANCE")
matrix_account = os.getenv("MATRIX_USERNAME")
matrix_password = os.getenv("MATRIX_PASSWORD")
matrix_room_id = os.getenv("MATRIX_ROOM")


