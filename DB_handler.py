import psycopg2
import cert


class DB_handler():
    def __init__(self):
        self.con = psycopg2.connect(
            host="127.0.0.1",
            database="discord_project",
            user="postgres",
            password=cert.db_password
        )
        self.discord_http_interface = None

    def set_discord_http_interface(self, interface):
        self.discord_http_interface = interface

    def fetch_active_users_from_db(self):
        cur = self.con.cursor()
        cur.execute(f"SELECT u_id, img_id FROM voice_activity WHERE online='t'")
        row = cur.fetchall()
        cur.close()
        return int(row)

    def create_user(self, user_data, guild_id):
        cur = self.con.cursor()
        r = self.find_guild_id(guild_id)
        print(r[0])
        cur.execute(f"""
            INSERT INTO voice_activity(u_id, online, saved_datetime, img_id, guild_id) VALUES ({user_data['id']}, {user_data['online']}, current_timestamp, \'{user_data['img_id']}\', {r[0]});
        """)
        cur.close()
        self.con.commit()

    def find_guild_id(self, guild_id):
        cur = self.con.cursor()
        cur.execute(f"""
                            SELECT id FROM guild WHERE guild_id = {guild_id}
                        """)
        result = cur.fetchone()

        return result

    def find_which_guild_user_is_in(self, user_data):
        cur = self.con.cursor()
        cur.execute(f"""
                    SELECT g.id FROM guild AS g 
                        INNER JOIN voice_activity AS u 
                        ON g.id = u.guild_id WHERE u.u_id={user_data['id']}
                """)
        result = cur.fetchone()

        return result

    def user_set_online_state(self, user_data, state):
        cur = self.con.cursor()
        r = self.find_which_guild_user_is_in(user_data)
        print("res", r)
        cur.execute(f"""
            UPDATE voice_activity SET online={state} WHERE u_id={user_data['id']};
        """)
        cur.close()
        self.con.commit()

    def get_user_ids(self):
        return [x[1] for x in self.fetch_all()]

    def fetch_all(self):
        cur = self.con.cursor()
        cur.execute(f"""
                SELECT * FROM voice_activity;
                """)
        result = cur.fetchall()
        cur.close()
        self.con.commit()
        return result

    def get_data_guilds(self):
        cur = self.con.cursor()
        cur.execute(f"""
                        SELECT * FROM guild;
                        """)
        result = cur.fetchall()
        cur.close()
        self.con.commit()
        return [{"id": r[1], "name": r[2]} for r in result]

    def create_guild(self, guild_data):
        cur = self.con.cursor()
        cur.execute(f"""
                    INSERT INTO guild (guild_id, guild_name) VALUES ({guild_data['id']}, \'{guild_data['name']}\');
                    """)
        cur.close()
        self.con.commit()
