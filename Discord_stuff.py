import requests
from tornado.websocket import websocket_connect
import json
import asyncio
import datetime
from cert import *

my_loop = asyncio.get_event_loop()


DISCORD_HELLO_OBJECT = {"op": 2, "d": {
    "token": bot_token, "intents": 640, "properties":
        {"$os": "linux", "$browser": "disco", "$device": "disco"}
     }}


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


def create_discord_http(db):
    return DiscordHttp(db)


class DiscordHttp:
    def __init__(self, db):
        self.db = db
        db.set_discord_http_interface(self)
        self.bot_headers = {
                            "User-Agent": "DiscordBot($url, $versionNumber)",
                            "Authorization": f"Bot {bot_token}",
                            }

    def get_user_data(self, user_id):
        requested_data = requests.get(f"https://discord.com/api/v8/users/{user_id}", headers=self.bot_headers)
        return requested_data.json()

    def update_guilds(self):
        guilds = requests.get("https://discord.com/api/v8/users/@me/guilds", headers=self.bot_headers)
        recorded_guilds = self.db.get_data_guilds()
        print(guilds.json())
        print(recorded_guilds)
        #u = self.db.find_which_guild_user_is_in
        for guild_data in guilds.json():
            if guild_data['id'] not in [g['id'] for g in recorded_guilds]:
                self.db.create_guild(guild_data)



def create_discord_ws(function=None, database=None):
    discord_ws = DiscordWsHandler()
    discord_ws.set_functional_interface(function, database)
    return discord_ws


class DiscordWsHandler:
    def __init__(self):
        self.connection = None
        self.sequence_number = None
        self.functional_interface = None
        asyncio.ensure_future(self.get_con(), loop=my_loop)

    def set_functional_interface(self, functional_interface: str, db) -> None:
        assert functional_interface is not None, \
            print(f"{functional_interface} is not a valid functional interface")
        self.functional_interface = interface_factory(functional_interface, db)

    async def get_con(self) -> None:
        ws = await websocket_connect("wss://gateway.discord.gg/?v=6&encoding=json")
        self.connection = ws
        asyncio.ensure_future(self.send_handshake_and_start_pinging(ws), loop=my_loop)
        await self.await_messages()

    async def send_handshake_and_start_pinging(self, ws) -> None:
        """ uzycie self.connection == ws mi sie nie podoba. """
        ws.write_message(json.dumps(DISCORD_HELLO_OBJECT))
        while self.connection == ws:
            self.connection.write_message(json.dumps({"op": 1, "d": self.sequence_number}))
            await asyncio.sleep(41.25)

    async def await_messages(self) -> None:
        if self.connection:
            assert self.functional_interface, print("Feature not implemented")
            while msg := await self.connection.read_message():
                print(msg)
                msg = json.loads(msg)
                assert msg['op'] != 9, await self.get_con()
                self.functional_interface.interpret_data(msg)


def interface_factory(type_of_message, db):
    if type_of_message == "VOICE_STATE_OBSERVER":
        return VoiceStateObserver(db)


class VoiceStateObserver:
    def __init__(self, db):
        self.db = db

    def interpret_data(self, msg):
        if msg['t'] == "VOICE_STATE_UPDATE":
            usr = UserObject(msg['d'])
            if msg['d']['channel_id'] is None:
                self.db.user_set_online_state(usr.get_data(), False)
            else:
                db_data = [x for x in self.db.fetch_all()]
                if int(msg['d']['user_id']) in [int(u[1]) for u in db_data]:
                    self.db.user_set_online_state(usr.get_data(), True)
                    pass
                else:
                    self.db.create_user(usr.get_data(), msg['d']['guild_id'])

class GuildStateObserver:
    def __init__(self, db):
        self.db = db

    def interpret_data(self, msg):
        if msg['t'] == "GUILD_MEMBER_UPDATE":
            if msg['d']['user']['id'] == bot_id:
                usr = UserObject(msg['d'])
            if msg['d']['channel_id'] is None:
                self.db.user_set_online_state(usr.get_data(), False)
            else:
                db_data = [x for x in self.db.fetch_all()]
                if int(msg['d']['user_id']) in [int(u[1]) for u in db_data]:
                    self.db.user_set_online_state(usr.get_data(), True)
                    pass
                else:
                    self.db.create_user(usr.get_data())
