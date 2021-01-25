import psycopg2
import cert


class DB_handler():
    def __init__(self):
        self.con = psycopg2.connect(
            host="127.0.0.1",
            database="discord_project",
            user="postgres",
            password=cert.toSamoHasloCoDoBankuUzywam
        )
        self.discord_http_interface = None

    def set_discord_http_interface(self, interface):
        self.discord_http_interface = interface

    def fetch_active_users_from_db(self):
        cur = self.con.cursor()
        cur.execute(f"SELECT u_id, img_id FROM voice_activity WHERE online='t'")
        row = cur.fetchall()
        cur.close()
        return row

    def create_user(self, user_data):
        cur = self.con.cursor()
        cur.execute(f"""
            INSERT INTO voice_activity(u_id, online, saved_datetime, img_id) VALUES ({user_data['id']}, {user_data['online']}, current_timestamp, \'{user_data['img_id']}\');
        """)
        cur.close()
        self.con.commit()

    def user_set_online_state(self, user_data, state):
        cur = self.con.cursor()
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
