from matrix_client.client import MatrixClient


def send_message_to_matrix(m_server, m_account, m_password, m_room_id, m_content):
    """ Send a message to a matrix room
    parameters:
    server : string - The name of the server.  e.g. "https://matrix.example.org"
    account : string - The name of the account e.g. "@alice:example.org"
    password : string - The password for the account e.g. "my-secret-password"
    room_id : string - The id of the room e.g. "!my-fave-room:example.org"
    content : string - The content of the message e.g. "Hello World!"
    """

    # Create a Matrix client instance
    client = MatrixClient(m_server)

    # Log in
    # client.login_with_password(username=m_account, password=m_password)
    client.login(username=m_account, password=m_password, sync=True)

    # Get a room instance
    room = client.join_room(m_room_id)

    # Send a message synchronously
    response = room.send_text(text=m_content)

    # Wait for the response before continuing
    # response.wait_for_response()
    client.logout()
