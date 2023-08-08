import asyncio

from nio import AsyncClient, MatrixRoom, RoomMessageText

async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    """ Not currently used"""
    print(
        f"Message received in room {room.display_name}\n"
        f"{room.user_name(event.sender)} | {event.body}"
    )


async def send_message_to_matrix(server, account, password, room_id, content) -> None:
    """ Send a message to a matrix room
    parameters:
    server : string - The name of the server.  e.g. "https://matrix.example.org"
    account : string - The name of the account e.g. "@alice:example.org"
    password : string - The password for the account e.g. "my-secret-password"
    room_id : string - The id of the room e.g. "!my-fave-room:example.org"
    content : string - The content of the message e.g. "Hello World!"
    """


    client = AsyncClient(server, account)
    # client.add_event_callback(message_callback, RoomMessageText)  #Not currently used

    # print(await client.login(password))
    await client.login(password)
    "Logged in as @alice:example.org device id: RANDOMDID"

    # If you made a new room and haven't joined as that user, you can use
    # await client.join("your-room-id")

    await client.room_send(
        # Watch out! If you join an old room you'll see lots of old messages
        room_id=room_id,
        message_type="m.room.message",
        content={"msgtype": "m.text", "body": content},
    )
    await client.sync_forever(timeout=5000)  # milliseconds
    await client.close()


