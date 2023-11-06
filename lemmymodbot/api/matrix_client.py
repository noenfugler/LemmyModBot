from typing import List, Dict

from matrix_client.client import MatrixClient


class MatrixFacade:
    server: str
    account: str
    password: str

    def __init__(self, server: str, account: str, password: str):
        self.server = server
        self.account = account
        self.password = password

    def send_message(self, room_id: str, content: str):
        client = MatrixClient(self.server)
        client.login(username=self.account, password=self.password, sync=True)
        room = client.join_room(room_id)
        room.send_text(text=content)
        client.logout()

    def report(self, flags: List[str], extras: Dict[str, str], content: str) -> str:
        matrix_message = '\n\nMod bot (with L plates) : ' + ', '.join(flags)
        matrix_message = matrix_message + '\n' + str(extras)
        matrix_message = matrix_message + '\n' + content
        return matrix_message
