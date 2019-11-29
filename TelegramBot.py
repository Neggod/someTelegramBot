#!/usr/bin/env python3

import telebot
from telebot import types
from ModuleParser import IG_stories_and_post_Parser
from LessonModule import Lesson, User, has_next_lesson, get_user
from settings import TOKEN, LINK_IG, NAME, HEADERS, ADMINS_ID

bot = telebot.TeleBot(TOKEN)
ADD_NEW_LESSON = False
NEW_LESSON = Lesson(new_lesson=True)
STEP = 0


@bot.message_handler(commands=['start'])
def send_welcome(message):
    get_user(message.chat.id, first_name=message.chat.first_name)
    print(NAME, LINK_IG, message.chat.first_name)
    text = "`Приветствую тебя`, *{2}*. \n*Подписывайся* на мой Instagram: [{0}]({1})".format(
        NAME, LINK_IG, message.chat.first_name)
    print(text)
    button = set_buttons()
    bot.send_message(message.chat.id, text, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=button)


@bot.message_handler(commands=['help'])
def help_message(message):
    if message.chat.id not in ADMINS_ID:
        text = '*Приветствую, {0}!*\n Данный бот создан, прежде всего, как площадка' \
           ' для прохождения курса китайского языка.'.format(message.chat.first_name)
        button = set_buttons(course='Начать обучение', last_post='Instagram')
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=button)
    else:
        text = '*Приветствую, госпожа*\n `Приказывай`'
        button = set_buttons(edit='Редактировать урок', add='Добавить урок')
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=button)


@bot.message_handler(commands=['info'])
def send_info(message):
    text = "`Приветствую тебя`. *Подписывайся* на мой Instagramm: [{0}]({1})".format(NAME, LINK_IG)
    bot.send_message(message.chat.id, text, parse_mode='Markdown', disable_web_page_preview=True)


@bot.message_handler(commands=['last_post'])
def send_last_post(message):
    ig_parser = IG_stories_and_post_Parser(LINK_IG, HEADERS)
    text = '*Последний пост* `доступен по `[ссылке]({0})'.format(ig_parser.get_last_post())
    bot.send_message(message.chat.id, text, parse_mode='Markdown')


def set_buttons(**kwargs):
    button = types.InlineKeyboardMarkup()
    help_btn = types.InlineKeyboardButton('Помощь', callback_data='/help')
    if not kwargs:
        button.add(help_btn)
        return button
    for callback, text in kwargs.items():
        btn = types.InlineKeyboardButton(text, callback_data=callback)
        button.add(btn)
    return button


@bot.message_handler(commands=['course'])
def get_course(message):
    button = set_buttons(next='Читать далее')
    current_lesson = Lesson(message.chat.id)
    if isinstance(current_lesson.lesson, str):
        bot.send_message(message.chat.id, current_lesson.lesson)
        return
    if current_lesson.audio_id:
        bot.send_voice(message.chat.id, current_lesson.audio_id)
    if current_lesson.image_id:
        bot.send_photo(message.chat.id, current_lesson.image_id)
    if has_next_lesson(message.chat.id):
        bot.send_message(message.chat.id, '*{0}. {1}* \n\n {2}'.format(
        current_lesson.theme_id, current_lesson.theme, current_lesson.text_lesson),
                    parse_mode='Markdown', reply_markup=button)
        current_lesson.get_next_lesson(message.chat.id)
    else:
        print(current_lesson.text_lesson)
        bot.send_message(message.chat.id, current_lesson.text_lesson)
        return


@bot.callback_query_handler(func=lambda call: True)
def get_next_lesson(call):
    if call.data in ['next', 'course']:
        if not has_next_lesson(call.message.chat.id):
            return
        get_course(call.message)
    elif call.data == 'last_post':
        send_last_post(call.message)
    elif call.data == 'help':
        bot.send_message(call.message.chat.id, 'Куку')
        help_message(call.message)
    elif call.data == 'add':
        add_lesson(call.message)
    elif call.data == 'edit':
        edit_lesson(call.message)

def add_lesson(message):
    global ADD_NEW_LESSON, STEP
    ADD_NEW_LESSON = True
    if not NEW_LESSON.theme:
        bot.send_message(message.chat.id, 'Введите тему')
        STEP += 1
    elif not NEW_LESSON.text_lesson and NEW_LESSON.theme:
        bot.send_message(message.chat.id, 'Введите текст урока')
        STEP += 1
    elif not NEW_LESSON.audio_id and STEP == 2:
        bot.send_message(message.chat.id, 'Отправьте аудиофайл для урока или НЕТ для пропуска элемента'
                                          ' (аудиофайла) или СТОП для просмотра введенных данных текущего урока')
        STEP += 1
    elif not NEW_LESSON.image_id and STEP == 3:
        bot.send_message(message.chat.id,
                         'Отправьте изображение для урокаили НЕТ для пропуска элемента'
                         ' (изображения) или СТОП для просмотра введенных данных текущего урока')
        STEP += 1
    elif STEP == 5:
        bot.send_message(message.chat.id,
                         '*{0}*\n\n {1}\n\nЧтобы сохранить урок напиши ДОБАВИТЬ'.format(
                             NEW_LESSON.theme, NEW_LESSON.text_lesson), parse_mode='Markdown')


def edit_lesson(message):
    bot.send_message(message.chat.id, "Пока думаю над логикой")


@bot.message_handler(content_types=['text', 'voice', 'photo'])
def echo_all(message):
    global ADD_NEW_LESSON, STEP
    if message.chat.id in ADMINS_ID and ADD_NEW_LESSON:
        if STEP == 5 and message.text.upper() == 'ДОБАВИТЬ':
            NEW_LESSON.add_lesson()
            STEP = 0
            ADD_NEW_LESSON = False
            NEW_LESSON.clear()
        if message.text and message.text.upper() == "СТОП":
            print('STOP')
            STEP = 5
            if NEW_LESSON.theme and NEW_LESSON.text_lesson:
                if NEW_LESSON.image_id:
                    bot.send_photo(message.chat.id, NEW_LESSON.image_id)
                if NEW_LESSON.audio_id:
                    bot.send_voice(message.chat.id, NEW_LESSON.audio_id)
                bot.send_message(message.chat.id, '*{0}*\n\n {1}\n\nЧтобы сохранить урок напиши ДОБАВИТЬ'.format(NEW_LESSON.theme, NEW_LESSON.text_lesson), parse_mode='Markdown')
            else:
                NEW_LESSON.clear(True)
                STEP = 0
        if STEP == 1:
            NEW_LESSON.theme = message.text
        if STEP == 2:
            NEW_LESSON.text_lesson = message.text
        if STEP == 3:
            print(message.voice)
            if message.voice:
                print(message.voice.file_id)
                NEW_LESSON.audio_id = message.voice.file_id
            elif message.text:
                if message.text.upper() == 'НЕT':
                    STEP = 4
                else:
                    STEP -= 1
        if STEP == 4:
            if message.photo:
                print(message.photo[0])
                NEW_LESSON.image_id = message.photo[0].file_id
                STEP = 5
            elif message.text:
                if message.text.upper() == 'НЕТ':
                    STEP = 5
                else:
                    STEP -= 1
        add_lesson(message)
    else:
        help_message(message)


if __name__ == '__main__':
    bot.polling(none_stop=True, timeout=100)
