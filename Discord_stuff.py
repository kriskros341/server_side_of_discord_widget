from tornado.websocket import websocket_connect
from abstract_stuff import AbstractStateObserver, SingletonDecorator
from DbHandler import get_db
from typing import *
from cert import *
import requests
import datetime
import asyncio
import json


my_loop = asyncio.get_event_loop()


DISCORD_HELLO_OBJECT = {"op": 2, "d": {
    "token": bot_token, "intents": 640, "properties":
        {"$os": "linux", "$browser": "disco", "$device": "disco"}
     }}


class UserObject:
    def __init__(self, msg_data: Dict[str, Any]):
        self.id = msg_data['user_id']
        self.avatar = msg_data['member']['user']['avatar']
        self.voice_state = self.set_voice_state(msg_data)
        self.saved_time = datetime.datetime.now().timestamp()
        self.db = get_db()

    @staticmethod
    def set_voice_state(msg_data: Dict[str, Any]) -> bool:
        if msg_data['channel_id'] is None:
            return False
        else:
            return True

    def get_data(self) -> Dict[str, Any]:
        return {"id": self.id, "online": self.voice_state, "saved_datetime": self.saved_time, "img_id": self.avatar}


def create_discord_http_api():
    return DiscordHttp()


class DiscordHttp:
    def __init__(self) -> None:
        self.db_handler = get_db()
        self.db_handler.set_discord_http_interface(self)
        self.bot_headers = {
                            "User-Agent": "DiscordBot($url, $versionNumber)",
                            "Authorization": f"Bot {bot_token}",
                            }

    def get_user_data_by_id(self, user_id) -> Dict[str, Any]:
        requested_data = requests.get(f"https://discord.com/api/v8/users/{user_id}", headers=self.bot_headers)
        return requested_data.json()

    def get_data_of_active_users(self):
        r = []
        for u_id in self.db_handler.fetch_ids_of_active_users():
            r.append(self.get_user_data_by_id(u_id))
        return r

    def update_guilds(self):
        guilds = requests.get("https://discord.com/api/v8/users/@me/guilds", headers=self.bot_headers)
        recorded_guilds = self.db_handler.get_data_guilds()
        for guild_data in guilds.json():
            if guild_data['id'] not in [g['id'] for g in recorded_guilds]:
                self.db_handler.create_guild(guild_data)


def create_discord_ws(functional_interface=None):
    assert functional_interface is not None, f"{functional_interface} is not a valid functional interface"
    discord_ws = DiscordWsHandler()
    discord_ws.set_functional_interface(functional_interface)
    return discord_ws


class DiscordWsHandler:
    def __init__(self):
        self.connection = None
        self.sequence_number = None
        self.session_id = None
        self.functional_interface = None
        self.discord_hello = DISCORD_HELLO_OBJECT
        self.connect()

    def set_functional_interface(self, functional_interface: str) -> None:
        """
        creates data interpreter
        set intents that specify events we want to listen for in our ws
        """
        self.functional_interface = create_api_interface(functional_interface)
        self.discord_hello['d']['intents'] = self.functional_interface.required_intents

    async def get_con(self):
        """
        save connection in state and return it's copy.
        We will use the copy to break the ping-pong loop if new connection is established
        """
        ws = await websocket_connect("wss://gateway.discord.gg/?v=6&encoding=json")
        self.connection = ws
        await self.send_handshake_and_start_pinging(ws)

    async def reconnect(self) -> None:
        """
        When WS disconnects for some reason, but session doesn't expire,
        it's possible to reconnect and get updated on missed events
        using opcode 6:reconnect.
        """
        self.connection.write_message(json.dumps({"op": 6, "d": {
            "token": bot_token, "session_id": self.session_id, "seq": self.sequence_number}}))

    async def send_handshake_and_start_pinging(self, ws) -> None:
        ws.write_message(json.dumps(self.discord_hello))
        print("msg1")
        while self.connection == ws:
            self.connection.write_message(json.dumps({"op": 1, "d": self.sequence_number}))
            await asyncio.sleep(41.25)

    async def await_messages(self) -> None:
        """
        an infinite loop that on read_message():
            updates the sequence number
            saves the session_id from READY message. It's required for reconnecting.
            checks for special opcodes, like 7:disconnected, 9:session_expired
            passes data to interpreter object
        """
        if self.connection:
            while msg := await self.connection.read_message():
                msg = json.loads(msg)
                print(msg)
                self.sequence_number = msg['s']
                if msg['op'] == 0:
                    self.session_id = msg['d']['session_id']
                assert msg['op'] != 7, await self.reconnect()
                assert msg['op'] != 9, await self.get_con()
                self.functional_interface.interpret_data(msg)
        else:
            """
            The connection sometimes needs time to kick in.
            """
            print("still connecting")
            await asyncio.sleep(1)
            return await self.await_messages()

    def connect(self):
        asyncio.ensure_future(self.get_con(), loop=my_loop)
        asyncio.ensure_future(self.await_messages(), loop=my_loop)


def create_api_interface(type_of_interface):
    if type_of_interface == "VOICE_STATE_OBSERVER":
        return VoiceStateObserver()
    if type_of_interface == "GUILD_MEMBER_UPDATE":
        return GuildStateObserver()


class VoiceStateObserver(AbstractStateObserver):
    def __init__(self):
        self.required_intents = 640
        self.db = get_db()

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


class GuildStateObserver(AbstractStateObserver):
    def __init__(self):
        self.db = get_db()

    def interpret_data(self, msg):
        if msg['t'] == "GUILD_MEMBER_UPDATE":
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
