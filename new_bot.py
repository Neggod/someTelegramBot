#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import datetime
import os
import time

import requests
import telebot
from telebot.types import Message

from Worker import Worker
from telebot import types, apihelper
from configparser import ConfigParser
import logging

ADMINS_ID = [216584376, 168037636]
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

worker = Worker(1)
# Если будет работать через прокси - вместо None надо вставить {'https': 'https://адрес_прокси:порт_прокси'}
# apihelper.proxy = {'https': 'https://127.0.0.1:8888'}
bot = telebot.TeleBot('854264208:AAES4xVOauTJBivQT75atRrl_-0yY2Ow68c', threaded=False)

file = 'BQACAgIAAxkBAAIJOl5qha71aNUpp4yzq2ZxW7pyCfd5AAJhBQACZCJZS0fdtTzmqClxGAQ'


@bot.message_handler(commands=['start', 'help'])  # DONE
def start_message(mess: types.Message):
    print("FIRST CHECK USER")
    if not worker.check_user(mess.chat.id, mess.chat.username):
        print(f"NEW USER {mess.chat.username}")
    text = "Спасибо за активацию!\nБот в разработке до 25 марта, " \
           "пока ознакомьтесь с моим чек-листом"
    bot.send_document(mess.chat.id, file, caption=text, parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.chat.id not in ADMINS_ID)  # DONE
def close_channel(m):
    print(m)
    bot.send_message(m.chat.id, "Я пока не готов")


@bot.message_handler(func=lambda m: m.chat.id in ADMINS_ID)
def commands(m: Message):  # FUCKING TODO
    print(m)
    if m.text.startswith("!"):
        text = worker.get_users()
        bot.send_message(m.chat.id, text)


if __name__ == '__main__':
    counter = 0
    bot.infinity_polling()
    bot.polling(none_stop=True, timeout=120)
