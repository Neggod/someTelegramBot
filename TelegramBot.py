#!/usr/bin/env python3

import telebot
from telebot import types, apihelper
from ModuleParser import IG_stories_and_post_Parser
from LessonModule import Lesson, Theme, get_themes, get_user
from settings import TOKEN, LINK_IG, NAME, HEADERS, ADMINS_ID, PROXY

apihelper.proxy = PROXY
bot = telebot.TeleBot(TOKEN)
ADD_NEW_LESSON = False
NEW_LESSON = None
STEP = 0
USER_THEME = {}


def nothing_func(call):
    print("QQ")
    pass


@bot.message_handler(commands=['start'])
def send_welcome(message):
    print(message.chat.id, message.chat.first_name)
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
def send_last_post(call):
    ig_parser = IG_stories_and_post_Parser(LINK_IG, HEADERS)
    text = '*Последний пост* `доступен по `[ссылке]({0})'.format(ig_parser.get_last_post())
    bot.send_message(call.message.chat.id, text, parse_mode='Markdown')


def set_buttons(row_mode=False, **kwargs):
    button = types.InlineKeyboardMarkup()
    help_btn = types.InlineKeyboardButton('Помощь', callback_data='/help')
    if not kwargs:
        button.add(help_btn)
        return button
    if row_mode:
        btn = []
        for callback, text in kwargs.items():
            btn.append(types.InlineKeyboardButton(text, callback_data=callback))
            if len(btn) == 2:
                button.row(*btn)
                btn = []
        if btn:
            button.row(*btn)
        return button
    for callback, text in kwargs.items():
        btn = types.InlineKeyboardButton(text, callback_data=callback)
        button.add(btn)
    return button


def send_lesson_message(chat_id, lesson: Lesson, theme: str, current_lesson: int, theme_lenght: int, markup):
    if lesson.lesson_image:
        bot.send_photo(chat_id, lesson.lesson_image)
    if lesson.lesson_voice:
        bot.send_voice(chat_id, lesson.lesson_voice)
    text = "*{0}\nУрок {1}/{2}*\n\n{3}".format(theme, current_lesson, theme_lenght, lesson.text)
    if not theme:
        text = lesson.text
    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)


def get_themes_list(call):
    text = '*Выберите тему:*'
    themes = get_themes()
    callback = {}
    for theme in themes:
        key = "!{0}".format(theme)
        callback[key] = theme
    markup = set_buttons(**callback)
    bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=markup)


@bot.message_handler(commands=['course'])
def get_course(message):
    get_themes_list(message)


def get_first_lesson(call):
    if not call.data.startswith("!"):
        get_themes_list(call)
    else:
        theme = Theme(call.data[1:], call.message.chat.id)
        USER_THEME[call.message.chat.id] = theme
        first_lesson = USER_THEME[call.message.chat.id].get_first_lesson()
        markup = set_buttons(next='Дальше >>')
        send_lesson_message(call.message.chat.id, first_lesson, theme.theme, theme.current_lesson,
                            len(theme) - 1, markup)


def check_next_lesson(call, **kwargs):
    user_theme = USER_THEME.get(call.message.chat.id)
    if not user_theme:
        get_first_lesson(call)
        user_theme = USER_THEME.get(call.message.chat.id)
    lesson = USER_THEME.get(call.message.chat.id).next_lesson()
    if len(user_theme) > 1:

        markup = set_buttons(row_mode=True, prev='<< Назад', next='Дальше>>', **kwargs)
        send_lesson_message(call.message.chat.id, lesson, user_theme.theme,
                            user_theme.current_lesson, len(user_theme) - 1, markup)
    else:

        markup = set_buttons(get_themes="Выберите следующую тему", send_last_post="Последний пост в Instagram",
                             donate="Поддержать проект")
        send_lesson_message(call.message.chat.id, lesson, None, None, None, markup)


def check_prev_lesson(call, **kwargs):
    user_theme = USER_THEME.get(call.message.chat.id)
    if not user_theme:
        get_first_lesson(call)
    else:
        lesson = user_theme.prev_lesson()
        if user_theme.current_lesson > 1:
            markup = set_buttons(row_mode=True, prev='<< Назад', next='Дальше>>', **kwargs)
            send_lesson_message(call.message.chat.id, lesson, user_theme.theme,
                                user_theme.current_lesson, len(user_theme) - 1, markup)
        elif user_theme.current_lesson == 1:
            markup = set_buttons(next='Дальше >>')
            send_lesson_message(call.message.chat.id, lesson, user_theme.theme,
                                user_theme.current_lesson, len(user_theme) - 1, markup)
        else:
            get_first_lesson(call)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    CALLBACK = {
        'next': check_next_lesson,
        'prev': check_prev_lesson,
        'send_last_post': send_last_post,
        'get_themes': get_themes_list,
        'empty': nothing_func,
        'add': add_new_theme,
        'edit': edit_theme,
    }
    if call.data.startswith('!'):
        get_first_lesson(call)
    CALLBACK.get(call.data, nothing_func)(call)


#         if not has_next_lesson(call.message.chat.id):
#             return
#         get_course(call.message)
#     elif call.data == 'last_post':
#         send_last_post(call.message)
#     elif call.data == 'help':
#         bot.send_message(call.message.chat.id, 'Куку')
#         help_message(call.message)
#     elif call.data == 'add':
#         add_lesson(call.message)
#     elif call.data == 'edit':
#         edit_lesson(call.message)


# def add_lesson(message):
#     global ADD_NEW_LESSON, STEP
#     ADD_NEW_LESSON = True
#     if not NEW_LESSON.theme:
#         bot.send_message(message.chat.id, 'Введите тему')
#         STEP += 1
#     elif not NEW_LESSON.text_lesson and NEW_LESSON.theme:
#         bot.send_message(message.chat.id, 'Введите текст урока')
#         STEP += 1
#     elif not NEW_LESSON.audio_id and STEP == 2:
#         bot.send_message(message.chat.id, 'Отправьте аудиофайл для урока или НЕТ для пропуска элемента'
#                                           ' (аудиофайла) или СТОП для просмотра введенных данных текущего урока')
#         STEP += 1
#     elif not NEW_LESSON.image_id and STEP == 3:
#         bot.send_message(message.chat.id,
#                          'Отправьте изображение для урокаили НЕТ для пропуска элемента'
#                          ' (изображения) или СТОП для просмотра введенных данных текущего урока')
#         STEP += 1
#     elif STEP == 5:
#         bot.send_message(message.chat.id,
#                          '*{0}*\n\n {1}\n\nЧтобы сохранить урок напиши ДОБАВИТЬ'.format(
#                              NEW_LESSON.theme, NEW_LESSON.text_lesson), parse_mode='Markdown')

def add_new_theme(call):
    pass


def edit_theme(call):
    pass


# @bot.message_handler(content_types=['text', 'voice', 'photo'])
# def echo_all(message):
#     global ADD_NEW_LESSON, STEP
#     if message.chat.id in ADMINS_ID and ADD_NEW_LESSON:
#         if STEP == 5 and message.text.upper() == 'ДОБАВИТЬ':
#             NEW_LESSON.add_lesson()
#             STEP = 0
#             ADD_NEW_LESSON = False
#             NEW_LESSON.clear()
#         if message.text and message.text.upper() == "СТОП":
#             print('STOP')
#             STEP = 5
#             if NEW_LESSON.theme and NEW_LESSON.text_lesson:
#                 if NEW_LESSON.image_id:
#                     bot.send_photo(message.chat.id, NEW_LESSON.image_id)
#                 if NEW_LESSON.audio_id:
#                     bot.send_voice(message.chat.id, NEW_LESSON.audio_id)
#                 bot.send_message(message.chat.id,
#                                  '*{0}*\n\n {1}\n\nЧтобы сохранить урок напиши ДОБАВИТЬ'.format(NEW_LESSON.theme,
#                                                                                                 NEW_LESSON.text_lesson),
#                                  parse_mode='Markdown')
#             else:
#                 NEW_LESSON.clear(True)
#                 STEP = 0
#         if STEP == 1:
#             NEW_LESSON.theme = message.text
#         if STEP == 2:
#             NEW_LESSON.text_lesson = message.text
#         if STEP == 3:
#             print(message.voice)
#             if message.voice:
#                 print(message.voice.file_id)
#                 NEW_LESSON.audio_id = message.voice.file_id
#             elif message.text:
#                 if message.text.upper() == 'НЕT':
#                     STEP = 4
#                 else:
#                     STEP -= 1
#         if STEP == 4:
#             if message.photo:
#                 print(message.photo[0])
#                 NEW_LESSON.image_id = message.photo[0].file_id
#                 STEP = 5
#             elif message.text:
#                 if message.text.upper() == 'НЕТ':
#                     STEP = 5
#                 else:
#                     STEP -= 1
#         add_lesson(message)
#     else:
#         help_message(message)


if __name__ == '__main__':
    bot.polling(none_stop=True, timeout=100)
