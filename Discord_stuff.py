import requests
from tornado.websocket import websocket_connect
import json
import asyncio
import datetime
my_loop = asyncio.get_event_loop()

BOT = "NzcxMDA3MTI1Mjc4OTQ5NDE3.X5l2Vw.78cX5mxVfEVAdKz8mgiFv0hWo8U"  #irek MjE0NjQ4NDQ0NzY4MjIzMjMy.Xg-dAA.7VrWSRCstTcr0Mu2LeZC5ZC6rCw
DISCORD_HELLO_OBJECT = {"op": 2,"d": {"token": BOT, "intents": 640, "properties": { "$os": "linux", "$browser": "disco", "$device": "disco"}}}


class UserObject:
    def __init__(self, msg_data):
        self.id = msg_data['user_id']
        self.avatar = msg_data['member']['user']['avatar']
        self.voice_state = self.set_voice_state(msg_data)
        self.saved_time = datetime.datetime.now().timestamp()

    @staticmethod
    def set_voice_state(msg_data):
        if msg_data['channel_id'] is None:
            return False
        else:
            return True

    def get_data(self):
        return {"id": self.id, "online": self.voice_state, "saved_datetime": self.saved_time, "img_id": self.avatar}


class UserList:
    def __init__(self):
        self.users = []

    def add_user(self, user_data):
        self.users.append(user_data)

    def remove_user(self, user_data):
        self.users.pop(self.users.index(next(user for user in self.users if user['id'] == user_data['id'])))


my_users = UserList()


def create_discord_http(auth_token, db):
    return DiscordHttp(auth_token, db)


class DiscordHttp:
    def __init__(self, auth_token, db):
        db.set_discord_http_interface(self)
        self.bot_headers = {
                            "User-Agent": "DiscordBot($url, $versionNumber)",
                            "Authorization": f"Bot {auth_token}",
                            }

    def get_user_data(self, user_id):
        requested_data = requests.get(f"https://discord.com/api/v8/users/{user_id}", headers=self.bot_headers)
        return requested_data.json()


def create_discord_ws(user_list, db):
    return DiscordWsHandler(user_list, db)

def on_ping(ws, *data):
    print("print", *data)


class DiscordWsHandler:
    def __init__(self, user_list, db):
        self.db_interface = db
        self.user_list = my_users
        self.connection = None
        self.connections = []
        self.sequence_number = None
        asyncio.ensure_future(self.get_con_and_start_loop(), loop=my_loop)

    async def get_con_and_start_loop(self):
        print("connecting")
        ws = await websocket_connect("wss://gateway.discord.gg/?v=6&encoding=json")
        self.connection = ws
        await ws.write_message(json.dumps(DISCORD_HELLO_OBJECT))
        asyncio.ensure_future(self.take_care_of_pinging(ws), loop=my_loop)
        await self.start_loop()

    async def restart_connection(self):
        self.connection.close()

    async def take_care_of_pinging(self, ws):

        while True:
            if self.connection != ws:
                break
            print(ws)
            await asyncio.sleep(40)
            self.connection.ping(json.dumps({"op": 1, "d": self.sequence_number}))

    async def start_loop(self):
        if self.connection:
            print(self.connection)
            while msg := await self.connection.read_message():
                msg = json.loads(msg)
                assert msg['op'] != 9, await self.get_con_and_start_loop()
                self.sequence_number = msg['s']
                print(msg)
                if msg['t'] == "VOICE_STATE_UPDATE":
                    usr = UserObject(msg['d'])
                    if msg['d']['channel_id'] is None:
                        self.db_interface.user_set_online_state(usr.get_data(), False)
                    else:
                        db_data = [x for x in self.db_interface.fetch_all()]
                        if int(msg['d']['user_id']) in [int(u[1]) for u in db_data]:
                            self.db_interface.user_set_online_state(usr.get_data(), True)
                            pass
                        else:
                            self.db_interface.create_user(usr.get_data())
