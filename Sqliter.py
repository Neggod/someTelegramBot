import time
from configparser import ConfigParser
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_name = 'users.db'
create_script = """BEGIN TRANSACTION;
	PRAGMA foreign_keys = on;

	CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER DEFAULT 1 PRIMARY KEY AUTOINCREMENT,
	"chat_id"	INTEGER DEFAULT 0 UNIQUE,
	"username"	TEXT
	);
	COMMIT;"""


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

