import tornado.ioloop
import tornado.web
from tornado.websocket import WebSocketHandler, websocket_connect
from DB_handler import DB_handler
import json
import asyncio
from Discord_stuff import *

PORT = 2137

db = DB_handler()
active_connections = []
user_list = []

def test1(con_list, data):
    print(f"data to {con_list}")
    for controller in con_list:
        controller.write_message(json.dumps({"text":data}))


class HTTPController(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db

    def check_origin(self, origin):
        return True

    def get(self):
        active_users = self.db.fetch_active_users_from_db()
        self.write(json.dumps({"active":active_users}))


class Controller(WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
        self.con_list = active_connections
        active_connections.append(self)
        self.discord_ws = discord_ws
        self.discord_ws.connections.append(self)
        self.discord_http = discord_http


    def check_origin(self, origin):
        return True


    def open(self):
        self.write_message(json.dumps({"msg": "ok"}))

    def on_message(self, msg):
        msg = json.loads(msg)
        if msg['option'] == "fetch_all":
            data = db.fetch_users_active_from_db()
            data = json.dumps({"msg":"user_data", "id":data[0], "username":data[1]})
            self.write_message(data)
        if msg['option'] == "state_of_discord":
            data = self.discord_http.get_user_data(267460142889566209)
            self.write_message({"msg": "user_data", "data":data})


def make_app():
    return tornado.web.Application([
        (r"/status", HTTPController),
        (r"/testing", Controller),
    ])



if __name__ == "__main__":
    app = make_app()
    app.listen(PORT)
    print(f"Listening localhost on {PORT}")
    discord_http = create_discord_http(BOT, db)
    discord_ws = create_discord_ws(user_list, db)
    asyncio.ensure_future(discord_ws.start_loop(), loop=my_loop)


    tornado.ioloop.IOLoop.current().start()
    print("test")