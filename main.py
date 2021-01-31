import tornado.ioloop
import tornado.web
from tornado.websocket import WebSocketHandler, websocket_connect
from DbHandler import get_db
import json
import asyncio
from Discord_stuff import *
from typing import *

PORT = 2137


class HTTPController(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = get_db()

    def check_origin(self, origin):
        return True

    def get(self):
        active_users = self.db.fetch_active_users_from_db()
        self.write(json.dumps({"active": active_users}))



class WebsocketControllerObserver:
    def __init__(self):
        self.controller_list = []

    def remove_controller(self, controller):
        self.controller_list.pop(self.controller_list.index(controller))

    def add_controller(self, controller):
        self.controller_list.append(controller)


class WebsocketWebsocketController(WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observer = None
        self.db_handler = None
        self.discord_http_api_handler = None
        self.prepare_interfaces()

    def prepare_interfaces(self):
        self.db_handler = db
        self.observer = observer
        observer.add_controller(self)
        self.discord_http_api_handler = create_discord_http_api()

    def check_origin(self, origin):
        return True

    def open(self):
        self.write_message(json.dumps({"msg": "ok"}))

    def on_message(self, msg):
        msg = json.loads(msg)
        if msg['option'] == "fetch_all":
            test = self.db_handler.fetch_ids_of_active_users()
            data = json.dumps([{"msg": "user_data", "id": data[0], "username": data[1]} for data in test])
            self.write_message(data)
        if msg['option'] == "state_of_discord":
            data = self.discord_http_api_handler.get_data_of_active_users()
            self.write_message({"msg": "user_data", "data": data})

    def on_close(self):
        self.observer.remove_controller(self)

def make_app():
    return tornado.web.Application([
        (r"/status", HTTPController),
        (r"/testing", WebsocketWebsocketController),
    ])


if __name__ == "__main__":
    db = get_db()
    observer = WebsocketControllerObserver()
    app = make_app()
    app.listen(PORT)

    print(f"Listening localhost on {PORT}")
    discord_http = create_discord_http_api()
    discord_http.update_guilds()

    discord_ws = create_discord_ws(functional_interface="VOICE_STATE_OBSERVER")
    tornado.ioloop.IOLoop.current().start()
