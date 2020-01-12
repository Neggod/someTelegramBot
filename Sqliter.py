import time
from configparser import ConfigParser
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cfg_name = os.path.join(BASE_DIR, 'config.ini')

parser = ConfigParser()
parser.read(cfg_name)
create_script = parser.get('sqlite_db', 'create_db')
db = parser.get('sqlite_db', 'name')


class SQLiter:

    def __init__(self, db_name):
        self.db = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.db.cursor()
        with self.db:
            self.cursor.executescript(create_script)
            self.db.commit()

    def add_user(self, chat_id, username):
        while True:
            try:
                with self.db:
                    self.cursor.execute('INSERT OR IGNORE INTO users (chat_id, username) VALUES (?, ?)',
                                        (chat_id, username))
                    self.db.commit()
                break
            except sqlite3.ProgrammingError:
                print("wait")
                time.sleep(2)

    def get_all_users(self):
        while True:
            try:
                with self.db:
                    self.cursor.execute("SELECT chat_id FROM users")
                return self.cursor.fetchall()
            except sqlite3.ProgrammingError:
                print("wait")
                time.sleep(2)

    def get_user(self, chat_id):
        while True:
            try:
                with self.db:
                    self.cursor.execute("SELECT username FROM users WHERE chat_id = ?", (chat_id,))
                user = self.cursor.fetchone()
                if user:
                    user = user[0]
                return user
            except sqlite3.ProgrammingError:
                print('wait')
                time.sleep(2)

    def update_user(self, chat_id, username):
        while True:
            try:

                with self.db:
                    self.cursor.execute('UPDATE users SET username = ? WHERE chat_id = ?', (username, chat_id))
                    self.db.commit()
                break
            except sqlite3.ProgrammingError:
                print("wait")

    def add_new_channel(self, name_channel, link_channel, description, owner_id,
                        subscribers, ads_cost, time_in_top_tape, pr,
                        date_of_last_post, message_id,
                        notice=None, chat_id=None, views_per_post=None, er=None):
        args = (chat_id, name_channel, link_channel, owner_id, description,
                subscribers, views_per_post, er, ads_cost, time_in_top_tape, pr,
                notice, date_of_last_post, message_id)
        while True:
            try:
                with self.db:
                    self.cursor.execute(
                        "INSERT OR REPLACE INTO channels_post (chat_id, name_channel, link_channel, "
                        "owner_id, description,"
                        "subscribers, views_per_post, er, ads_cost, time_in_top_tape, pr, notice,"
                        "date_of_last_post, message_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", args)
                    self.db.commit()
                print(f"Channel {name_channel} added successfully in {date_of_last_post}")
                break
            except sqlite3.ProgrammingError:
                print("wait")
                time.sleep(2)

    def get_channel(self, link_channel):
        while True:
            try:
                with self.db:
                    self.cursor.execute("SELECT * FROM channels_post WHERE link_channel = ?", (link_channel,))
                print("get channel", link_channel)
                return self.cursor.fetchone()
            except sqlite3.ProgrammingError:
                print("wait")
                time.sleep(2)

    def get_last_post(self, channel_name):
        while True:
            try:
                with self.db:
                    self.cursor.execute(
                        "SELECT date_of_last_post, message_id FROM channels_post WHERE name_channel = ?",
                        (channel_name,))
                print("get channel", channel_name)
                return self.cursor.fetchone()
            except sqlite3.ProgrammingError:
                print("WAIT")
                time.sleep(2)

    def set_time_of_last_post(self, channel_name, date, message_id):
        while True:
            try:
                with self.db:
                    self.cursor.execute(
                        "UPDATE channels_post SET date_of_last_post = ?, message_id = ? WHERE name_channel = ?",
                        (date, message_id, channel_name))
                    self.db.commit()
                break
            except sqlite3.ProgrammingError:
                print("WAIT")
                time.sleep(2)

    def drop_channels(self):
        with self.db:
            self.cursor.execute("delete from channels_post")
            self.cursor.execute('delete from users')
            self.db.commit()


if __name__ == '__main__':
    db = SQLiter(db)
    db.drop_channels()
