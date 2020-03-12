#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import datetime
from collections import defaultdict

from Sqliter import SQLiter
from configparser import ConfigParser
from bs4 import BeautifulSoup as bs
import requests
import os, time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cfg_name = os.path.join(BASE_DIR, 'config.ini')

parser = ConfigParser()
parser.read(cfg_name)

db_name = 'users.db'
create_script = """BEGIN TRANSACTION;
	PRAGMA foreign_keys = on;

	CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER DEFAULT 1 PRIMARY KEY AUTOINCREMENT,
	"chat_id"	INTEGER DEFAULT 0 UNIQUE,
	"username"	TEXT
	);
	COMMIT;"""


class User:

    def __init__(self, chat, username):
        self.chat_id = chat
        self.username = username
        self.target_url = None
        self.bad_target = set()
        self.target = None

    def __str__(self):
        return f"USER: {self.username}"

    def __repr__(self):
        return f"USER: {self.username}"

    def clear(self):
        self.target_url = None
        self.bad_target.clear()
        self.target = None


class Worker:

    def __init__(self, time_limit=0):
        self.db = SQLiter(os.path.join(BASE_DIR, db_name))
        self.users = {}
        self.channels = defaultdict(dict)
        self.__time_limit = time_limit

    def check_user(self, chat_id, username=None):
        if not self.users.get(chat_id):
            print(f'NO USER {username} IN MEMO')
            old_username = self.db.get_user(chat_id)
            if not old_username:
                self.users[chat_id] = User(chat_id, username)
                self.db.add_user(chat_id, username)
                print(f"ADD NEW USER {username} TO DB")
                return False
            elif old_username == username or not username:
                self.users[chat_id] = User(chat_id, old_username)
                print(f"HAS USER {old_username} IN DB")
                return True
            else:
                self.users[chat_id] = username
                self.db.update_user(chat_id, username)
                print(f'USER {username} CHANGE NAME')
                return True
        else:
            print(f"USER {username} IN MEMO")
            return True

    def get_users(self):
        users = self.db.get_all_users()
        text = ''
        for user in users:
            text += str(user[0]) + ', '
        print(text)
        return text[:-2]
