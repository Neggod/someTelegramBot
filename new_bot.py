import datetime
import os
import time

import requests
import telebot

from Worker import Worker, WorkerError
from telebot import types, apihelper
from configparser import ConfigParser
import logging

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cfg_name = os.path.join(BASE_DIR, 'config.ini')

parser = ConfigParser()
parser.read(cfg_name)
token = parser.get('Telegram', 'token')
main_channel_link = parser.get('Telegram', 'main_channel_link')
main_channel_id = parser.get('Telegram', 'main_channel_id')
main_channel_name = f"[{parser.get('Telegram', 'main_channel_name')}]({main_channel_link})"
check_chat_id = parser.get('Telegram', 'check_chat_id')
check_chat_link = parser.get('Telegram', 'check_chat_link')
check_chat_name = f"[{parser.get('Telegram', 'check_chat_name')}]({check_chat_link})"
admin = parser.get('Telegram', 'admin')
worker = Worker(int(parser.get('Telegram', 'time_limit')))
apihelper.proxy = None  # {'https': 'https://127.0.0.1:8888'}
bot = telebot.TeleBot(token, num_threads=3)
bot_name = '@' + bot.get_me().username.replace("_", "\_")
ALL_CATEGORIES = ["Медицина", "Еда и рецепты", "Семья и отношения", "Блоги", "Красота и мода", "Новости", "Здоровье",
                  "Животные", "Наука и образование", "Видео и фильмы", "Бизнес и заработок", "Книги",
                  "Игры и приложения", "Фото и искусство", "Музыка", "Сливы и курсы", "Политика", "Продажи",
                  "Путешествия и туры", "Работа и вакансии", "Ремонт и строительство", "Telegram", "Ставки и спорт",
                  "Чаты ", "IT (Технологии)", "Цитаты", "Гороскопы и эзотерика", "Экономика", "Дизайн", "Авто",
                  "Юмор и развлечения", "Другое", "Религии", "Криптовалюты", "Языки", "Психология",
                  "Маркетинг и реклама", "Рукоделие", "Лайфхаки"]


class InputDataError(Exception):
    pass


def set_buttons(bad_target: set = None, pattern=None, **kwargs):
    """
    Create inline keyboard.
    """
    patterns = {'default': "НЕ ДЛЯ КНОПКИ!", 'send': "Отправить рекламу", "add_channel": "Добавить объявление",
                'ads_cost': "Указать стоимость рекламы", 'self_piar': "Наличие взаимопиара", 'uncheck': "Не проверять",
                'time': "Указать время в ТОПЕ/ЛЕНТЕ", "edit": "Редактировать объявление", 'ready': "Верно",
                'categories': "Выбрать категорию", 'notice': 'Добавить примечание', 'check': 'Пройти проверку',
                'next': 'Дальше', 'prev': 'Назад'}
    not_needed = ['default', 'edit', 'next', 'prev', 'ready', 'send', 'add_channel', 'check', 'uncheck']
    button = types.InlineKeyboardMarkup()
    if bad_target:
        print(f"BAD TARGET - {bad_target}")
        bad_target.update(not_needed)
    else:
        bad_target = set(not_needed)
    if len(bad_target) == len(patterns):
        button.add(types.InlineKeyboardButton('Опубликовать', callback_data='send'))
        return button
    elif len(bad_target) == (len(patterns) - 1) and 'notice' not in bad_target:
        button.row(types.InlineKeyboardButton(patterns['notice'], callback_data='notice'),
                   types.InlineKeyboardButton('Опубликовать', callback_data='send'))
        return button

    if pattern == 'admin':
        if not kwargs:
            button.add(types.InlineKeyboardButton('Разослать всем сообщение', callback_data='send all'))
            button.add(types.InlineKeyboardButton('Настроить медленный режим', callback_data='time limit'))
            return button
        else:
            for k, v in kwargs.items():
                button.add(types.InlineKeyboardButton(k, callback_data=v))
            return button

    if pattern and pattern not in patterns:
        pattern = 'default'

    if not kwargs and not pattern:
        button.add(types.InlineKeyboardButton("Посмотреть объявления", url=check_chat_link))
        button.add(types.InlineKeyboardButton("Добавить объявленние", callback_data='add_channel'))
        return button
    elif kwargs and pattern in patterns:
        rows = dict.fromkeys(('prev', 'ready', 'next'))
        multirows = []
        multirows_ = []
        value = f"{pattern}"
        if 'link' in kwargs:
            value += " " + f'{kwargs["link"]}'
            kwargs.pop('link')
        if kwargs:
            value += ' ' + '{0}'
            for k, v in kwargs.items():
                if k == 'next' or k == 'prev' or k == 'ready':
                    name, *val = v.split(' ', 1)
                    if name in patterns:
                        print(name)
                        rows[k] = (types.InlineKeyboardButton(patterns[name], callback_data=value.format(v)))
                    elif name and val:
                        rows[k] = (types.InlineKeyboardButton(name, callback_data=value.format(*val)))
                    else:
                        rows[k] = (types.InlineKeyboardButton(name, callback_data=k))
                elif pattern == 'time':
                    if len(multirows) == 3:
                        button.row(*multirows)
                        button.add(types.InlineKeyboardButton(v, callback_data=value.format(k)))
                        multirows.clear()
                    else:
                        multirows.append(types.InlineKeyboardButton(v, callback_data=value.format(k)))
                elif pattern == 'categories':
                    if len(multirows) == 3:
                        button.row(*multirows)
                        multirows.clear()
                    if len(multirows_) == 2:
                        button.row(*multirows_)
                        multirows_.clear()
                    if len(v) < 6:
                        multirows.append(types.InlineKeyboardButton(v, callback_data=value.format(k)))
                    elif len(v) < 11:
                        multirows_.append(types.InlineKeyboardButton(v, callback_data=value.format(k)))
                    else:
                        button.add(types.InlineKeyboardButton(v, callback_data=value.format(k)))
                else:
                    multirows.append(types.InlineKeyboardButton(k, callback_data=value.format(v)))
            if multirows:
                button.row(*multirows)
            temp_row = []
            if rows['prev']:
                temp_row.append(rows['prev'])
            if rows['ready']:
                temp_row.append(rows['ready'])
            if rows['next']:
                temp_row.append(rows['next'])
            if temp_row:
                button.row(*temp_row)

        else:
            button.add(types.InlineKeyboardButton(patterns[pattern], callback_data=value))
        return button  # DONE!
    if not kwargs and pattern == 'self_piar':
        button.row(types.InlineKeyboardButton("Да", callback_data='self_piar 1'),
                   types.InlineKeyboardButton("Нет", callback_data='self_piar 0'))
        return button

    if not kwargs and pattern == 'default':
        button = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button.add(types.KeyboardButton('Посмотреть объявления'))
        button.add(types.KeyboardButton('Добавить объявление'))
        return button
    if not kwargs and pattern == 'edit':
        print(f'PATTERN EDIT WITH {bad_target}')
        for k, v in patterns.items():
            if k in bad_target:
                continue
            button.add(types.InlineKeyboardButton(v, callback_data=k))
        return button
    if not kwargs and pattern == 'send':
        button.add(types.InlineKeyboardButton(patterns[pattern], callback_data=pattern))
        button.add(types.InlineKeyboardButton(patterns['edit'], callback_data='edit'))
        return button
    if not kwargs and pattern == 'check':
        button.add(types.InlineKeyboardButton(patterns[pattern], callback_data='check'))
        button.add(types.InlineKeyboardButton(patterns['uncheck'], callback_data='uncheck'))
        return button


def check_chats(user_id):
    check = False
    try:
        print(check_chat_id, "CHAT ID")

        channel_status = bot.get_chat_member(main_channel_id, user_id).status
        print(f"CHANNEL {channel_status}")
        chat_status = bot.get_chat_member(check_chat_id, user_id).status
        print(f"CHAT {chat_status}")

        if channel_status == chat_status and chat_status in ['member', 'creator', 'administrator']:
            check = True
        print(check)
        return check
    except telebot.apihelper.ApiException as err:
        print(err)
        return check


def check_user_group(chat_id, user_id, link, new_channel=True):
    '''
    get args return tuple(text for message, btn)
    Args:
        new_channel: 
        chat_id: may be int (chat_id), or @str(for open chats).=)
        user_id:
        link:

    Returns:

    '''
    big_btn = set_buttons(pattern='default')
    chat_ = total = None
    if new_channel:
        btn = set_buttons(pattern='ready', **{'ready': f'Исправил add_channel {chat_.id}'})
        try:
            print(f"USER {worker.users[user_id].username} TRY PARSING DATA FROM CHANNEL {chat_id}")
            chat_ = bot.get_chat(chat_id)
            btn = set_buttons(pattern='ready', **{'ready': f'Исправил add_channel {chat_.id}'})
            print(chat_)
            total = bot.get_chat_members_count(chat_.id)
            if total < 1000:
                return "В вашем канале меньше 1000 подписчиков.", big_btn
            if not chat_.description or (chat_.description and not worker.users[user_id].username in chat_.description):

                print(f"USER {worker.users[user_id].username} NOT IN DESCRIPTION OF CHAT {chat_.title}")
                for chat_member in bot.get_chat_administrators(chat_.id):
                    print(chat_member.user.id, "IS ADMIN")

                    if chat_member.user.id == user_id:
                        print(f'{worker.users[user_id]} - админ чата {chat_.title}')
                        break
                    else:
                        print(chat_member.user.username, f' - админ чата {chat_.title}')
                else:
                    print(f" {worker.users[user_id]} IS NOT ADMIN OF CHAT {chat_.title}")
                    worker.users[user_id].target = 'add_channel'
                    text = f"Вы не являетесь администратором группы {chat_.title}, " \
                           f"нужно добавить свой @username в описание канала" \
                           f"и нажать на кнопку, чтобы продолжить"
                    return text, btn
            if not worker.channels[user_id][link].subscribers:
                worker.channels[user_id][link].subscribers = total
            if not worker.channels[user_id][link].name:
                worker.channels[user_id][link].name = chat_.title
            if not worker.channels[user_id][link].chat_id:
                worker.channels[user_id][link].chat_id = chat_.id
            if not chat_.type == 'channel':
                worker.channels[user_id][link].chat_status = "Группа"

        except telebot.apihelper.ApiException:
            print(f"SLY {worker.users[user_id]} FORWARD MESSAGE BUT DON`T ADD IN CHANNEL")
            worker.users[user_id].target = 'add_channel'
            text = (f"Так как это закрытый канал или группа - необходимо добавить туда {bot_name}, и:\n "
                    f"-*Переслать мне какое-нибудь сообщение с канала, если это канал*.\n"
                    f"-*Написать в группе любое сообщение, если это группа*.")
            return text, btn
    
    post = worker.channels[user_id][link].create_post(worker.users[user_id].username)
    worker.users[user_id].bad_target = worker.channels[user_id][link].create_bad_target
    btn = set_buttons(pattern='edit', bad_target=worker.users[user_id].bad_target)
    return post, btn


@bot.message_handler(commands=['start', 'help'])  # DONE
def start_message(mess):
    print("FIRST CHECK USER")
    btn = set_buttons(pattern='default')
    text = "Спасибо за активацию!\nВыберите пункт меню👇🏻"
    bot.send_message(mess.chat.id, text, parse_mode='Markdown', reply_markup=btn)


@bot.message_handler(content_types=['text'],
                     func=lambda m: m.chat.id > 0 and not m.forward_from_chat and m.text and m.text.startswith(
                         'https://t.me/joinchat/'))  # DONE
def close_channel(m):
    print(f"CHECK PRIVATE CHANNEL BY {m.chat.username}")
    big_btn = set_buttons(pattern='default')
    if not m.chat.username:
        worker.users[m.chat.id].target = 'username'
        btn = set_buttons(pattern='ready', **{'ready': 'Добавил'})
        bot.send_message(m.chat.id, "Необходимо добавить @username в настройках телеграм.", reply_markup=btn)

    elif worker.check_user(m.chat.id, m.chat.username):
        if m.text.count(" "):
            link = m.text.split(' ', 1)
        else:
            link = m.text

        worker.users[m.chat.id].clear()
        worker.users[m.chat.id].target_url = link
        print("CHECK PRIVATE CHANNEL LINK. TRY CHECK DB OR PARSING")
        m_id = bot.send_message(m.chat.id, f'Проверяю ваш канал {m.text}', # DELETE THIS MESSAGE LATER
                         disable_web_page_preview=True, reply_markup=big_btn).message_id
        status = worker.check_channel(link, m.chat.id, m.chat.username)
        if status == 0 and worker.channels[m.chat.id][link].chat_id:
            print(f"PRIVATE CHANNEL OF {m.chat.username} IN DB OR IN MEMO")
            text, btn = check_user_group(worker.channels[m.chat.id][link].chat_id, m.chat.id, link, new_channel=False)
            time_ = datetime.datetime.fromtimestamp(worker.channels[m.chat.id][link].date_of_last_post)
            now = datetime.datetime.now()
            if (now - time_).seconds // (60 * 60) >= worker.limit:
                worker.users[m.chat.id].target = 'send'
            else:
                text = f"Посты можно отправлять не чаще одного раза в {worker.limit} часов."
                worker.users[m.chat.id].clear()
                btn = big_btn
            bot.delete_message(m.chat.id, m_id)
            bot.send_message(m.chat.id, text, reply_markup=btn, parse_mode='Markdown',
                             disable_web_page_preview=True)

        else:
            print(f"PRIVATE CHANNEL OF {m.chat.username} NOT IN DB")
            # name_channel = ''
            # if worker.channels[m.chat.id][link].name:
            #     name_channel = worker.channels[m.chat.id][link].name.replace("_", "\_")
            # post = worker.channels[m.chat.id][link].create_post(m.chat.username)
            # # btn = set_buttons(pattern='edit')
            # 
            # bot.send_message(m.chat.id, f'Вот, что собрал о вашем канале {name_channel}: '
            #                             f'\n{post}', parse_mode="Markdown", reply_markup=big_btn,
            #                  disable_web_page_preview=True)
            # worker.users[m.chat.id].target = 'channel'
            # # else:
            # print(f"HAVEN`T PRIVATE CHANNEL OF {m.chat.username}")
            text = (f"Так как это закрытый канал или группа - необходимо добавить туда {bot_name}, и:\n "
                    f"-*Переслать мне какое-нибудь сообщение с канала, если это канал*.\n"
                    f"-*Написать в группе любое сообщение, если это группа*.")
            bot.edit_message_text(text, m.chat.id, m_id, reply_markup=big_btn)
            print(f"CHECK TELEMETR FOR {m.chat.username} WITH {link}")
            name, names = worker.parse_link(link)
            if name and not name == worker.channels[m.chat.id][link].name_channel:
                worker.channels[m.chat.id][link].name_channel = name
            if names:
                if names['Подписчиков']:
                    worker.channels[m.chat.id][link].subscribers = int(names['Подписчиков'].replace("'", ""))
                print(
                    f'ПОДПИСЧИКОВ {worker.channels[m.chat.id][link].name_channel} - {worker.channels[m.chat.id][link].subscribers}')
                worker.channels[m.chat.id][link].views_per_post = names["Просмотров на пост"]
                worker.channels[m.chat.id][link].er = names['ER'] if names['ER'] != '%' else None
            print(f"CHECK TELEMETR FOR {m.chat.username} WITH {link} IS OVER")
    else:
        print(f"USER {m.chat.username} SEND CLOSED CHANNEL, BUT HE NOT IN DB")
        btn = set_buttons(pattern='ready', **{'ready': "Подписался"})
        bot.send_message(m.chat.id, f"Чтобы добавить свой канал - нужно быть подписанными на"
                                    f" {main_channel_name} и {check_chat_name}",
                         parse_mode="Markdown", reply_markup=btn,
                         disable_web_page_preview=True)


@bot.message_handler(content_types=['text'], func=lambda m: m.chat.id > 0 and not m.forward_from_chat and m.text and (
        m.text.startswith("@") or (m.text.startswith("https://t.me"))
        and 'joinchat' not in m.text))  # DONE
def open_channel(m: types.Message):
    big_btn = set_buttons(pattern='default')
    if not m.chat.username:
        worker.users[m.chat.id].target = 'username'
        btn = set_buttons(pattern='ready', **{'ready': 'Добавил'})
        bot.send_message(m.chat.id, "Необходимо добавить @username в настройках телеграм.", reply_markup=btn)
    elif worker.check_user(m.chat.id, m.chat.username):
        print(f"GET OPEN CHANNEL LINK FROM USER {m.chat.username}")
        try:
            if m.text.count(' '):
                link = m.text.split(' ', 1)
                link = link if link.startswith('@') else ('@' + link.rsplit('/', 1)[-1])
            else:
                link = m.text if m.text.startswith('@') else ('@' + m.text.rsplit('/', 1)[-1])
            worker.users[m.chat.id].bad_target.clear()
            worker.users[m.chat.id].target_url = link
            m_id = bot.send_message(m.chat.id, f'Проверяю ваш канал {m.text}',  # DELETE THIS MESSAGE LATER
                                    disable_web_page_preview=True, reply_markup=big_btn).message_id
            status = worker.check_channel(link, m.chat.id, m.chat.username)
            
            if status == 0 and worker.channels[m.chat.id][link].chat_id:
                text, btn = check_user_group(link, m.chat.id, link, new_channel=False)
                print(f"PRIVATE CHANNEL OF {m.chat.username} IN DB OR IN MEMO")
                
                time_ = datetime.datetime.fromtimestamp(worker.channels[m.chat.id][link].date_of_last_post)
                now = datetime.datetime.now()
                if (now - time_).seconds // (60 * 60) >= worker.limit:
                    worker.users[m.chat.id].target = 'send'
                else:
                    text = f"Посты можно отправлять не чаще одного раза в {worker.limit} часов."
                    worker.users[m.chat.id].clear()
                    btn = big_btn
            else:
                text, btn = check_user_group(link, m.chat.id, link)
            bot.delete_message(m.chat.id, m_id)
            bot.send_message(m.chat.id, text, reply_markup=btn, parse_mode='Markdown',
                             disable_web_page_preview=True)
            print(f"CHECK TELEMETR FOR {m.chat.username} WITH {link}")
            name, names = worker.parse_link(link)
            if name and not name == worker.channels[m.chat.id][link].name_channel:
                worker.channels[m.chat.id][link].name_channel = name
            if names:
                if names['Подписчиков']:
                    worker.channels[m.chat.id][link].subscribers = int(names['Подписчиков'].replace("'", ""))
                print(
                    f'ПОДПИСЧИКОВ {worker.channels[m.chat.id][link].name_channel} - {worker.channels[m.chat.id][link].subscribers}')
                worker.channels[m.chat.id][link].views_per_post = names["Просмотров на пост"]
                worker.channels[m.chat.id][link].er = names['ER'] if names['ER'] != '%' else None
            print(f"CHECK TELEMETR FOR {m.chat.username} WITH {link} IS OVER")
                
            # chat = bot.get_chat(link)
            # print(f"GET CHAT {chat.title} VALUES")
            # if chat.description and m.chat.username in chat.description:
            #     print(f"USER {m.chat.username} IN CHAT {chat.title} DESCRIPTION")
            # 
            #     total = bot.get_chat_members_count(chat.id)
            #     if total < 1000:
            #         bot.send_message(m.chat.id, f'В вашем канале {link} меньше 1000 подписчиков', reply_markup=big_btn)
            #         worker.users[m.chat.id].bad_target.clear()
            #     else:
            #         bot.send_message(m.chat.id, f'Проверяю ваш канал {link}', reply_markup=big_btn)
            #         status = worker.check_channel(link, m.chat.id, m.chat.username)
            #         print(f"GET CHAT {chat.title} STATUS - {status}")
            #         if status == 0 and worker.channels[m.chat.id][link].chat_id:
            #             print(f"CHAT {chat.title} IN DB OR IN MEMO")
            #             time_ = datetime.datetime.fromtimestamp(worker.channels[m.chat.id][link].date_of_last_post)
            #             now = datetime.datetime.now()
            #             if (now - time_).seconds // (60 * 60) >= worker.limit:
            #                 post = worker.channels[m.chat.id][link].create_post(m.chat.username)
            #                 btn = set_buttons(pattern='send')
            #                 worker.users[m.chat.id].target = 'send'
            #             else:
            #                 post = f"Посты можно отправлять не чаще одного раза в {worker.limit} часов."
            #                 btn = big_btn
            #             print(f"SEND POST {chat.title}")
            #             bot.send_message(m.chat.id, post, reply_markup=btn, parse_mode="Markdown",
            #                              disable_web_page_preview=True)  # DONE
            #         elif status in [1, 2]:
            #             print(f"NEW CHAT {chat.title} AFTER PARSING")
            #             if not worker.channels[m.chat.id][link].subscribers:
            #                 worker.channels[m.chat.id][link].subscribers = total
            #             print(worker.channels[m.chat.id][link].subscribers)
            #             if not worker.channels[m.chat.id][link].name:
            #                 worker.channels[m.chat.id][link].name = chat.title
            #             if not worker.channels[m.chat.id][link].chat_id:
            #                 worker.channels[m.chat.id][link].chat_id = chat.id
            #             post = worker.channels[m.chat.id][link].create_post(m.chat.username)
            #             btn = set_buttons(pattern='edit', bad_target=worker.users[m.chat.id].bad_target)
            #             worker.users[m.chat.id].target = 'edit'
            #             if status == 1:
            #                 print(f"NEW CHAT {chat.title} AFTER PARSING TELEMETR")
            #                 bot.send_message(m.chat.id, f'Вот, что я собрал о вашем канале: \n{post}', reply_markup=btn,
            #                                  parse_mode="Markdown", disable_web_page_preview=True)
            #             elif status == 2:
            #                 print(f"NEW CHANNEL {chat.title} NOT TELEMETR")
            #                 print("SEND POST {chat.title}")
            #                 bot.send_message(m.chat.id, f'Вот, что я собрал о вашем канале '
            #                                             f'(Однако было бы больше, если бы вы добавили'
            #                                             f' его в https://telemetr.me): \n{post}', reply_markup=btn,
            #                                  parse_mode="Markdown", disable_web_page_preview=True)
            # 
            #         else:
            #             print("SOME EXCEPTION")
            #             raise InputDataError('Что-то не то ввели')
            # else:
            #     print(f"USER {m.chat.username} NOT IN CHAT {chat.title} DISCRIPTION")
            #     worker.users[m.chat.id].target = 'description'
            #     btn = set_buttons(pattern='ready', **{'ready': 'Добавил channel'})
            #     bot.send_message(m.chat.id, f"Необходимо добавить @{m.chat.username} описание канала {chat.title}, "
            #                                 "и нажать на кнопку, чтобы продолжить", reply_markup=btn)
            # 
        except telebot.apihelper.ApiException:
            print(f"USER {m.chat.username} INPUT BROKEN URL")
            worker.users[m.chat.id].clear()
            bot.send_message(m.chat.id, "Вы прислали некорректную ссылку. Попробуйте еще раз.")

    else:
        print(f"USER {m.chat.username} SEND OPEN CHANNEL, BUT HE NOT IN DB")
        btn = set_buttons(pattern='ready', **{'ready': "Подписался"})
        bot.send_message(m.chat.id, f"Чтобы добавить свой канал - нужно быть подписанными на"
                                    f" {main_channel_name} и {check_chat_name}",
                         parse_mode="Markdown", reply_markup=btn,
                         disable_web_page_preview=True)


class CallbackCommands:
    # users[chat_id] = User(chat_id)
    def add_channel(self, chat_id, mess_id, *args):  # ВРОДЕ DONE
        print(f"CALLBACK ADD CHANNEL")

        try:
            channel_id, *args = args
            if bot.get_chat_member(channel_id, chat_id).status == 'administrator' or \
                    (worker.users[chat_id].username in bot.get_chat(channel_id).description):
                print(f"USER {chat_id} IN OUR TARGET CHANNEL")
                link = worker.users[chat_id].target_url
                worker.users[chat_id].target = 'edit'
                post = worker.channels[chat_id][link].create_post(worker.users[chat_id].username)
                btn = set_buttons(pattern='edit')
                bot.edit_message_text('Вот что я собрал по вашему каналу:\n ' + post, chat_id, mess_id,
                                      reply_markup=btn, parse_mode='Markdown')
            else:
                print(f"USER {chat_id} NOT IN SELF TARGET CHANNEL")
                btn = set_buttons(pattern='defaulf')
                worker.users[chat_id].clear()
                bot.edit_message_text(f'Видимо вы нажали кнопку просто так. :)', chat_id, mess_id, reply_markup=btn)
        except telebot.apihelper.ApiException:
            print(f"USER {chat_id} CALL ADD CHANNEL NOT IN START OR HELP")
            btn = set_buttons()
            worker.users[chat_id].clear()
            bot.edit_message_text(f'Видимо вы нажали кнопку просто так. :)', chat_id, mess_id, reply_markup=btn)

    def send_post(self, chat_id, mess_id, *args):  # DONE
        print(f"CALLBACK SEND POST")

        if args and args[0] == 'all' and admin == worker.users[chat_id].username:
            if not worker.users[chat_id].target == 'send_all':
                worker.users[chat_id].target = 'send_all'
                bot.edit_message_text(f'Напиши мне сообщение, которое ты хотел бы отправить всем, @{admin}', chat_id,
                                      mess_id)
            else:
                counter_ = 0
                for user in worker.all_users():
                    if user == chat_id:
                        continue
                    bot.forward_message(user, chat_id, mess_id)
                    counter_ += 1
                    time.sleep(0.1)
                else:
                    bot.delete_message(chat_id, mess_id)
                    bot.send_message(chat_id, f"{counter_} сообщений доставлено!")
        else:
            link = worker.users[chat_id].target_url
            now = datetime.datetime.now()
            if worker.check_timer(chat_id, link, now):
                print(f"USER {chat_id} CAN SEND POST")
                post = worker.channels[chat_id][link].create_post(worker.users[chat_id].username)

                m_id = bot.send_message(check_chat_id, post, parse_mode="Markdown",
                                        disable_web_page_preview=True).message_id
                worker.users[chat_id].clear()
                worker.channels[chat_id][link].message_id = m_id
                print(f"USER {chat_id} SEND POST")
                worker.save_data_channel(chat_id, link)
                print(f"USER {chat_id} SAVE POST")
                text = f"Ваше объявление опубликовано в наш чат {check_chat_name}. " \
                       f"Если ваш канал не накручен? вы можете пройти проверку и ваше объявление будет размещено в " \
                       f"нашем канале {main_channel_name}."
                worker.users[chat_id].clear()
                btn = set_buttons(pattern='check')
                big_btn = set_buttons(pattern='default')
                m_id = bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=big_btn).message_id
                bot.delete_message(chat_id, m_id)
                bot.edit_message_text(text, chat_id, mess_id, parse_mode='Markdown', disable_web_page_preview=True,
                                      reply_markup=btn)
                try:
                    bot.leave_chat(worker.channels[chat_id][link].chat_id)
                except Exception:
                    pass
                return


            else:
                bot.edit_message_text(f"Посты можно отправлять не чаще одного раза в {worker.limit} часов.",
                                      chat_id, mess_id)
        return

    def edit_post(self, chat_id, mess_id, *args):
        btn = set_buttons(pattern='edit', bad_target=worker.users[chat_id].bad_target)
        bot.edit_message_reply_markup(chat_id, mess_id, reply_markup=btn)
        pass

    def prev(self, chat_id, message_id, *args):  # DONE
        if args and len(args) == 2:
            print(f'CORRECT ARGS {args}')
            if args[1].isdigit():
                val = int(args[1])
            else:
                val = args[1]
            self.CALLBACK[args[0]](chat_id, message_id, prev=val)
        else:
            print(f'INCORRECT ARGS {args}')

    def self_piar(self, chat_id, mess_id, *args):  # TODO
        print(f"CALLBACK SELF PIAR WITH {args}")
        if not args:
            text = "Делаете ли вы взаимопиар с другими каналами?"
            worker.users[chat_id].target = 'self_piar'
            btn = set_buttons(pattern='self_piar')
            bot.edit_message_text(text, chat_id, mess_id, reply_markup=btn)
        elif args[0].isdigit():
            value = int(args[0])
            link = worker.users[chat_id].target_url
            worker.channels[chat_id][link].pr = value
            print(f'SELF_PR {worker.channels[chat_id][link].pr} SET VALUE {value}')
            post = worker.channels[chat_id][link].create_post(worker.users[chat_id].username)
            worker.users[chat_id].bad_target.add('self_piar')
            worker.users[chat_id].target = 'edit'
            btn = set_buttons(pattern='edit', bad_target=worker.users[chat_id].bad_target)
            bot.edit_message_text(post, chat_id, mess_id, parse_mode='Markdown', disable_web_page_preview=True,
                                  reply_markup=btn)
        else:
            print(f"USER {chat_id} CHECK SELF PIAR VALUE {args} FOR CHAT {worker.users[chat_id].target_url}")
        return

    def ads_cost(self, chat_id, mess_id, *args):  # TODO
        print(f"CALLBACK ADS COST BY {worker.users.get(chat_id)}")
        link = worker.users[chat_id].target_url
        if not args:
            # worker.users[chat_id].bad_target.add('ads_cost')
            worker.users[chat_id].target = 'ads_cost'
            bot.delete_message(chat_id, mess_id)
            bot.send_message(chat_id, f"Укажите стоимость вашей рекламы, напишите только цифры."
                                      f"Помните, если вы укажите завышенную стоимость вашу рекламу не купят.",
                             parse_mode='Markdown', reply_markup=types.ReplyKeyboardRemove())
        else:
            if args[0].isdigit() and int(args[0]) == 1:
                worker.users[chat_id].bad_target.add('ads_cost')

            else:
                worker.users[chat_id].ads_cost = None
            post = worker.channels[chat_id][link].create_post(worker.users[chat_id].username)
            worker.users[chat_id].target = 'edit'
            btn = set_buttons(pattern='edit', bad_target=worker.users[chat_id].bad_target)
            bot.delete_message(chat_id, mess_id)
            bot.send_message(chat_id, post, parse_mode='Markdown', disable_web_page_preview=True,
                             reply_markup=btn)
        return

    def time(self, chat_id, mess_id, *args):  # VRODE TODO
        print(f"USER {chat_id} IN TIME WITH {args}")
        if args and 'limit' in args and worker.users[chat_id].username == admin:
            if not worker.users[chat_id].target == 'time_limit':
                worker.users[chat_id].target = 'time_limit'
                bot.edit_message_text(f'Напиши мне, через сколько часов должны публиковаться одинаковые каналы.',
                                      chat_id,
                                      mess_id)
            else:
                if len(args) > 1 and int(args[1]):
                    worker.set_limit(args[1])
                    bot.edit_message_text('Медленный режим успешно сохранён', chat_id, mess_id)
                else:
                    bot.edit_message_text(f'Оставили прежний режим: одно сообщение в {worker.limit} часов.',
                                          chat_id, mess_id)
            return

        top = ("1ч", "2ч", "3ч", "4ч", "5ч", "6ч", "12ч")
        tape = ("24ч", "36ч", "48ч", "52ч", "72ч", "Неделя", "Вечно")
        link = worker.users[chat_id].target_url
        if args:
            i = args[0]
        else:
            i = 0

        if not args:
            worker.users[chat_id].target = 'time'
            if not worker.channels[chat_id][link].time_in_top_tape:
                btn = set_buttons(pattern='time', **dict([(str(i), j) for i, j in enumerate(top)]))
                bot.edit_message_text("Укажите время размещения в топе вашего канала:",
                                      chat_id, mess_id, reply_markup=btn)
        elif not worker.channels[chat_id][link].time_in_top_tape and i:
            i = int(i)
            worker.channels[chat_id][link].time_in_top_tape = top[i]
            btn = set_buttons(pattern='time', **dict([(str(i), j) for i, j in enumerate(tape)]))
            bot.edit_message_text("Укажите время размещения в ленте вашего канала:",
                                  chat_id, mess_id, reply_markup=btn)
        elif worker.channels[chat_id][link].time_in_top_tape in top and i:
            i = int(i)
            worker.channels[chat_id][link].time_in_top_tape += ' / ' + tape[i]
            btn = set_buttons(pattern='ready', **{'ready': "Верно time 1", "prev": "Назад time 0"})
            bot.edit_message_text("Время размещения в топе/ленте: " + worker.channels[chat_id][link].time_in_top_tape,
                                  chat_id, mess_id, reply_markup=btn)
        elif worker.channels[chat_id][link].time_in_top_tape and worker.channels[chat_id][link].time_in_top_tape.count(
                '/'):
            if int(args[0]) == 0:
                worker.channels[chat_id][link].time_in_top_tape = None
            else:
                worker.users[chat_id].bad_target.add('time')
            post = worker.channels[chat_id][link].create_post(worker.users[chat_id].username)
            worker.users[chat_id].target = 'edit'
            btn = set_buttons(pattern='edit', bad_target=worker.users[chat_id].bad_target)
            bot.edit_message_text(post, chat_id, mess_id, parse_mode='Markdown', reply_markup=btn,
                                  disable_web_page_preview=True)
        return

    def notice(self, chat_id, mess_id, *args):
        link = worker.users[chat_id].target_url
        if worker.users[chat_id].target != 'notice':
            if not args:
                btn = set_buttons(pattern='notice', **{"Добавить примечание": 1, "Не добавлять": 0})
                bot.delete_message(chat_id, mess_id)
                bot.send_message(chat_id, 'Хотите ли вы добавить примечание для своего канала?',
                                 reply_markup=btn)
            elif args and int(args[0]):
                worker.users[chat_id].target = 'notice'
                bot.delete_message(chat_id, mess_id)
                bot.send_message(chat_id, 'Напишите мне примечание (не более 100 знаков), для своего объявления.',
                                 reply_markup=types.ReplyKeyboardRemove())
            else:
                worker.users[chat_id].target = 'edit'
                worker.users[chat_id].bad_target.add('notice')
                username = worker.users[chat_id].username
                post = worker.channels[chat_id][link].create_post(username)
                btn = set_buttons(pattern='edit', bad_target=worker.users[chat_id].bad_target)
                bot.edit_message_text(post, chat_id, mess_id, parse_mode='Markdown', reply_markup=btn,
                                      disable_web_page_preview=True)

        else:
            if args:
                worker.users[chat_id].target = 'edit'
                worker.users[chat_id].bad_target.add('notice')
            username = worker.users[chat_id].username
            post = worker.channels[chat_id][link].create_post(username)
            btn = set_buttons(pattern='edit', bad_target=worker.users[chat_id].bad_target)
            bot.edit_message_text(post, chat_id, mess_id, parse_mode='Markdown', reply_markup=btn,
                                  disable_web_page_preview=True)
        return

    def none_funk(self, chat_id, mess_id, *args):
        bot.send_message(chat_id, 'НЕ ШАЛИ!')
        return

    def categories(self, chat_id, mess_id, *args):  # TODO
        print(f"{worker.users[chat_id]} IN CALLBACK CATEGORIESD WITH ARGS {args}")
        link = worker.users[chat_id].target_url
        temp_list = []
        lenght = 0
        first_i = 0
        last_i = len(ALL_CATEGORIES) - 1
        target_i = None
        if args:
            target_i, *args = args

        if not args and target_i:
            if worker.users[chat_id].target != 'categories':

                if int(target_i):
                    worker.users[chat_id].bad_target.add('categories')
                else:
                    worker.channels[chat_id][link].description = None
                text = worker.channels[chat_id][link].create_post(worker.users[chat_id].username)
                btn = set_buttons(pattern="edit", bad_target=worker.users[chat_id].bad_target)
            else:
                worker.users[chat_id].target = 'edit'
                worker.channels[chat_id][link].description = ALL_CATEGORIES[int(target_i)]
                text = f"Вы выбрали категорию: {ALL_CATEGORIES[int(target_i)]}"
                btn = set_buttons(pattern='ready', **{'ready': 'Верно categories 1', 'prev': 'Назад categories 0'})
            bot.edit_message_text(text, chat_id, mess_id, parse_mode='Markdown', reply_markup=btn,
                                  disable_web_page_preview=True)
        else:
            worker.users[chat_id].target = 'categories'
            next_ = prev_ = None
            if target_i:
                target_i = int(target_i)
                start_i = int(args[0])
                prev_ = {'prev': f"Назад  {start_i} {target_i}"}
                first_i = target_i

            # for i in ALL_CATEGORIES[first_i: last_i]:
            #     lenght += len(i)
            #     if lenght > 90:
            #         tar_i = ALL_CATEGORIES.index(i)
            #         break
            #     temp_list.append(i)
            # else:
            #     tar_i = last_i
            # next_ = {'next': f'Дальше {tar_i} {first_i}'}

            # kb_buttons = dict([(str(i), j) for i, j in enumerate(temp_list, first_i)])
            kb_buttons = dict([(str(i), j) for i, j in enumerate(ALL_CATEGORIES)])
            #
            # if tar_i < last_i:
            #     kb_buttons.update(next_)
            # if first_i > 0 and prev_:
            #     kb_buttons.update(prev_)
            btn = set_buttons(pattern='categories', **kb_buttons)
            bot.edit_message_text('Выберите категорию канала:', chat_id, mess_id, reply_markup=btn)
        return

    def CALL(self, chat_id, mess_id, func, *args):  # DONE
        print(f'{worker.users.get(chat_id)} IN CALL WITH FUNC {func} AND ARGS {args}')
        username = worker.users[chat_id].username
        target = worker.users[chat_id].target
        link = worker.users[chat_id].target_url
        if func in ['ready', 'next', 'prev']:
            text = "Для того чтобы запустить объявление о продаже рекламы: \n" \
                   "— Ваш личный  юзернейм должен быть в информации о канале;\n" \
                   "— На канале должно быть более 999 подписчиков. \n" \
                   "Отправьте мне название вашего канала в формате @namechannel \n" \
                   "или ссылку на канал, если канал приветный."
            if args:
                call_func, *args = args

                if not call_func:
                    print(f'NESTED FUNC {func} WITHOUT ARGS')
                    # Проверки на нет узернаме и нет в чате
                    try:
                        if not username:
                            username = bot.get_chat(chat_id).username
                            if not username:
                                btn = set_buttons(pattern='ready', **{'ready': "Добавил"})
                                bot.delete_message(chat_id, mess_id)
                                bot.send_message(chat_id,
                                                 "По-прежнему необходимо добавить @username в настройках Telegram",
                                                 reply_markup=btn)
                            elif username and worker.check_user(chat_id, username):

                                bot.edit_message_text(text, chat_id, mess_id)
                                print(f"NEW USER {username} WAS UPDATED")
                        elif not check_chats(chat_id):
                            btn = set_buttons(pattern='ready', **{'ready': "Подписался"})
                            bot.delete_message(chat_id, mess_id)

                            bot.send_message(chat_id, f"Чтобы добавить свой канал - нужно быть подписанными на"
                                                      f" {main_channel_name} и {check_chat_name}",
                                             parse_mode="Markdown", reply_markup=btn,
                                             disable_web_page_preview=True)

                        else:
                            bot.edit_message_text(text, chat_id, mess_id)
                            print(f"NEW USER {username} WAS UPDATED")

                    except telebot.apihelper.ApiException:
                        btn = set_buttons(pattern='ready', **{'ready': "Подписался"})
                        bot.delete_message(chat_id, mess_id)

                        bot.send_message(chat_id, f"Чтобы добавить свой канал - нужно быть подписанными на"
                                                  f" {main_channel_name} и {check_chat_name}",
                                         parse_mode="Markdown", reply_markup=btn,
                                         disable_web_page_preview=True)
                        print(f"MAY BE USER {chat_id} BLOCKED US?")
                        print(f"CALLBACK CALL FUNC {func} WITHOUT ARGS")

                elif call_func:
                    if call_func == 'send':
                        if check_chats(chat_id):
                            self.CALLBACK.get(call_func, 'none_funk')(chat_id, mess_id, *args)
                        else:
                            btn = set_buttons(pattern='ready', **{'ready': "Подписался send"})
                            bot.edit_message_text(f"Чтобы добавить свой канал - нужно быть подписанными на"
                                                  f" {main_channel_name} и {check_chat_name}", chat_id, mess_id,
                                                  parse_mode="Markdown", disable_web_page_preview=True,
                                                  reply_markup=btn)
                    elif call_func == 'channel':
                        text = f"Так как это закрытый канал, необходимо добавить туда бота {bot_name} " \
                               f"и переслать ему оттуда какое-нибудь сообщение"
                        if worker.users[chat_id].target == call_func:
                            if worker.channels[chat_id][worker.users[chat_id].target_url].chat_id:
                                post = worker.channels[chat_id][worker.users[chat_id].target_url].create_post()
                                btn = set_buttons(pattern='edit', bad_target=worker.users[chat_id].bad_target)
                                bot.edit_message_text(post, chat_id, mess_id, parse_mode='Markdown',
                                                      disable_web_page_preview=True, reply_markup=btn)
                            elif worker.users[chat_id].target == 'description':
                                text = f"Необходимо добавить @{worker.users[chat_id].username}" \
                                       f"в описание канала и нажать на кнопку"
                                btn = set_buttons(pattern='ready', **{'ready': 'Добавил channel'})
                                bot.delete_message(chat_id, mess_id)
                                bot.send_message(chat_id, text, reply_markup=btn)
                            else:
                                btn = set_buttons(pattern='ready', **{'ready': 'Добавил channel'})
                                bot.delete_message(chat_id, mess_id)
                                bot.send_message(chat_id, text, reply_markup=btn)
                        else:
                            btn = set_buttons(pattern='ready', **{'ready': 'Добавил channel'})
                            bot.delete_message(chat_id, mess_id)
                            bot.send_message(chat_id, text, reply_markup=btn)
                    elif call_func.isdigit():
                        pass

                    else:
                        self.CALLBACK.get(call_func, 'none_funk')(chat_id, mess_id, *args)

                else:
                    btn = set_buttons()
                    bot.edit_message_text('Похоже я внезапно упал. Начнём сначала?', reply_markup=btn)
            elif not args:
                try:
                    if not username:
                        username = bot.get_chat(chat_id).username
                        if not username:
                            btn = set_buttons(pattern='ready', **{'ready': "Добавил"})
                            bot.delete_message(chat_id, mess_id)
                            bot.send_message(chat_id,
                                             "По-прежнему необходимо добавить @username в настройках Telegram",
                                             reply_markup=btn)
                            return
                        elif username and worker.check_user(chat_id, username):
                            bot.edit_message_text(text, chat_id, mess_id)
                            print(f"NEW USER {username} WAS UPDATED")
                            return
                    elif not check_chats(chat_id):
                        bot.delete_message(chat_id, mess_id)
                        btn = set_buttons(pattern='ready', **{'ready': "Подписался"})
                        bot.send_message(chat_id, f"Вы всё еще не подписаны на"
                                                  f" {main_channel_name} и {check_chat_name}",
                                         parse_mode="Markdown", reply_markup=btn,
                                         disable_web_page_preview=True)

                    else:
                        link = worker.users[chat_id].target_url
                        print(link)
                        if link:
                            if not worker.channels[chat_id].get(link):
                                bot.delete_message(chat_id, mess_id)
                                btn = set_buttons(pattern='ready', **{'ready': "Добавил"})

                                bot.send_message(chat_id, f"Необходимо добавить @{bot_name} в свой "
                                                          f"канал и переслать ему любое сообщение.", reply_markup=btn)
                                return
                            elif not worker.users[chat_id].username in bot.get_chat(
                                    worker.channels[chat_id][link].chat_id).description:
                                bot.delete_message(chat_id, mess_id)
                                btn = set_buttons(pattern='ready', **{'ready': "Добавил"})

                                bot.send_message(chat_id, f"Необходимо добавить в описание канала свой "
                                                          f"@{worker.users[chat_id].username}", reply_markup=btn)
                                return
                            else:
                                worker.users[chat_id].target = "edit"
                                btn = set_buttons(pattern="edit", bad_target=worker.users[chat_id].bad_target)
                                post = worker.channels[chat_id][link].create_post()
                                bot.edit_message_text(post, chat_id, mess_id, parse_mode='Markdown',
                                                      disable_web_page_preview=True, reply_markup=btn)
                                return

                        else:

                            text = "Для того чтобы запустить объявление о продаже рекламы: \n" \
                                   "— Ваш личный  юзернейм должен быть в информации о канале;\n" \
                                   "— На канале должно быть более 1000 подписчиков. \n" \
                                   "Отправьте мне название вашего канала в формате @namechannel \n" \
                                   "или ссылку на канал, если канал приватный."
                            bot.edit_message_text(text, chat_id, mess_id)
                    print(f"NEW USER {username} WAS CHECKED")
                except telebot.apihelper.ApiException:
                    btn = set_buttons(pattern='ready', **{'ready': "Подписался"})
                    bot.delete_message(chat_id, mess_id)

                    bot.send_message(chat_id, f"Чтобы добавить свой канал - нужно быть подписанными на"
                                              f" {main_channel_name} и {check_chat_name}",
                                     parse_mode="Markdown", reply_markup=btn,
                                     disable_web_page_preview=True)
                    print(f"MAY BE USER {chat_id} BLOCKED US?")
                    print(f"CALLBACK CALL FUNC {func} WITH ARGS")

        elif func in ('check', 'uncheck'):
            if func == 'check':
                text = f'Стоимость проверки и размещения канала в {main_channel_name}  - 50р. ' \
                       f'Для оплаты напишите @{admin}'
            else:
                text = f"Повторно разместить объявление вы можете через {worker.limit} часов"
            btn = set_buttons(pattern='default')
            bot.delete_message(chat_id, mess_id)
            bot.send_message(chat_id, text, parse_mode='Markdown',
                             disable_web_page_preview=True, reply_markup=btn)
        else:
            self.CALLBACK.get(func, 'none_funk')(chat_id, mess_id, *args)

        return

    def __init__(self):
        self.CALLBACK = {
            'add_channel': self.add_channel,
            'send': self.send_post,
            'edit': self.edit_post,
            'self_piar': self.self_piar,
            'ads_cost': self.ads_cost,
            'time': self.time,
            'categories': self.categories,
            'notice': self.notice,
            'none_funk': self.none_funk,
        }


CallComm = CallbackCommands()


@bot.callback_query_handler(func=lambda call: call)  # DONE
def get_callback(call):
    print(f"GET CALLBACK DATA {call.data} FROM USER {call.message.chat.username}")
    if not worker.users.get(call.message.chat.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        btn = set_buttons(pattern='default')
        bot.send_message(call.message.chat.id,
                         f"- Здесь публикуются только проверенные объявления {main_channel_name}\n"
                         f"- Здесь публикуются все объявления {check_chat_name}",
                         parse_mode="Markdown", disable_web_page_preview=True, reply_markup=btn)

    # worker.check_user(call.message.chat.id, call.message.chat.username)
    else:
        func, *args = call.data.split()
        CallComm.CALL(call.message.chat.id, call.message.message_id, func, *args)


@bot.message_handler(func=lambda m: m.chat.id > 0 and m.forward_from_chat,
                     content_types=['text', 'audio', 'document', 'photo', 'sticker', 'video', 'video_note',
                                    'voice', 'location', 'contact'])  # DONE
def forwarded_message(m):
    print(f"USER {m.chat.username} WITH URL "
          f"{worker.users.get(m.chat.id).target_url} FORVARD MESSAGE FROM CHANNEL {m.forward_from_chat.title}")
    # if worker.check_user(m.chat.id, m.chat.username):
    #     print(f"USER {m.chat.username} IS INITIATE")
    big_btn = set_buttons(pattern='default')
    if worker.users.get(m.chat.id) and worker.users[m.chat.id].target_url and worker.users[
        m.chat.id].target_url.startswith("https://t.me/joinchat"):
        print(f"USER {m.chat.username} YIELD IN VALUE LINK {worker.users[m.chat.id]} =)")
        link = worker.users[m.chat.id].target_url
        if link and worker.channels.get(m.from_user.id).get(link):
            text, btn = check_user_group(m.forward_from_chat.id, m.chat.id, link)
            bot.send_message(m.chat.id, text, reply_markup=btn, parse_mode='Markdown',
                             disable_web_page_preview=True)
            
            # try:
            #     print(f"USER {m.chat.username} TRY PARSING DATA FROM CHANNEL {m.forward_from_chat.title}")
            #     chat_ = bot.get_chat(m.forward_from_chat.id)
            #     print(chat_)
            #     total = bot.get_chat_members_count(chat_.id)
            #     if total < 1000:
            #         bot.send_message(m.chat.id, "В вашем канале меньше 1000 подписчиков.", reply_markup=big_btn)
            #         return
            #     if not worker.channels[m.chat.id][link].subscribers:
            #         worker.channels[m.chat.id][link].subscribers = total
            #     print(worker.channels[m.chat.id][link].subscribers)
            #     if not worker.channels[m.chat.id][link].name:
            #         worker.channels[m.chat.id][link].name = chat_.title
            #     if not worker.channels[m.chat.id][link].chat_id:
            #         worker.channels[m.chat.id][link].chat_id = chat_.id
            #     post = worker.channels[m.chat.id][link].create_post(m.chat.username)
            #     if chat_.description and m.chat.username in chat_.description:
            #         print(f"USER {m.chat.username} IN DESCRIPTION OF CHAT {chat_.title}")
            #         btn = set_buttons(pattern='edit')
            #         bot.send_message(m.chat.id, post, parse_mode='Markdown', reply_markup=btn,
            #                          disable_web_page_preview=True)
            #     else:
            #         print(f"USER {m.chat.username} NOT IN DESCRIPTION OF CHAT {chat_.title}")
            #         for chat_member in bot.get_chat_administrators(m.forward_from_chat.id):
            #             print(chat_member.user.id, "IS ADMIN")
            # 
            #             if chat_member.user.id == m.chat.id:
            #                 btn = set_buttons(pattern='edit')
            #                 bot.send_message(m.chat.id, post, parse_mode='Markdown', reply_markup=btn,
            #                                  disable_web_page_preview=True)
            #                 print()
            #                 break
            #             else:
            #                 print(chat_member.user.username, f' - админ чата {chat_.title}')
            #         else:
            #             print(f"USER {m.chat.username} NOT IN CHAT {chat_.title} DISCRIPTION AND NOT IN ADMINS")
            #             worker.users[m.chat.id].target = 'add_channel'
            #             btn = set_buttons(pattern='ready', **{'ready': f'Исправил add_channel {chat_.id}'})
            #             bot.send_message(m.chat.id, f"Вы не являетесь администратором группы {chat_.title}, "
            #                                         f"нужно добавить свой @username в описание канала"
            #                                         "и нажать на кнопку, чтобы продолжить", reply_markup=btn)
            # 
            # except telebot.apihelper.ApiException:
            #     print(f"SLY USER {m.chat.username} FORWARD MESSAGE BUT DON`T ADD IN CHANNEL")
            #     bot.send_message(m.chat.id, "Так как это закрытый канал, необходимо добавить меня в этот канал, "
            #                                 "и переслать мне какое-нибудь сообщение оттуда.")
        else:
            bot.leave_chat(m.chat.id)
    else:
        worker.users[m.chat.id].clear()
        text = "Для того чтобы запустить объявление о продаже рекламы: \n" \
               "— Ваш личный  юзернейм должен быть в информации о канале;\n" \
               "— На канале должно быть более 1000 подписчиков. \n" \
               "Отправьте мне название вашего канала в формате @namechannel \n" \
               "или ссылку на канал, если канал приватный."
        print(f"USER {m.chat.username} HAVEN'T CHAT LINK")
        bot.send_message(m.chat.id, text, reply_markup=big_btn)


@bot.message_handler(func=lambda m: m.chat.id > 0)
def commands(m):  # FUCKING TODO
    big_btn = set_buttons(pattern='defautl')
    if worker.check_user(m.chat.id, m.chat.username):
        target = worker.users[m.chat.id].target
        link = worker.users[m.chat.id].target_url
    else:
        target = None
        link = None

    if m.text == 'Посмотреть объявления':
        print("LOOK OBJAVA")
        bot.send_message(m.chat.id, f"- Здесь публикуются только проверенные объявления {main_channel_name}\n"
                                    f"- Здесь публикуются все объявления {check_chat_name}",
                         parse_mode="Markdown", disable_web_page_preview=True)
    elif m.text == 'Добавить объявление':
        print("ADD OBJAVA")
        if not m.chat.username:
            btn = set_buttons(pattern='ready', **{'ready': "Добавил"})
            m_id = bot.send_message(m.chat.id, "Необходимо добавить @username в настройках Telegram "
                                               "и нажать на кнопку, чтобы продолжить",
                                    reply_markup=btn).message_id
            bot.edit_message_reply_markup(m.chat.id, m_id, reply_markup=types.ReplyKeyboardRemove())
        else:
            if check_chats(m.chat.id):
                print(f"USER {m.chat.id} WAS SS")
                text = "Для того чтобы запустить объявление о продаже рекламы: \n" \
                       "— Ваш личный  юзернейм должен быть в информации о канале;\n" \
                       "— На канале должно быть более 1000 подписчиков. \n" \
                       "Отправьте мне название вашего канала в формате @namechannel \n" \
                       "или ссылку на канал, если канал приватный."
                bot.send_message(m.chat.id, text, reply_markup=types.ReplyKeyboardRemove())
            else:
                btn = set_buttons(pattern='ready', **{'ready': "Подписался"})
                bot.send_message(m.chat.id, f"Чтобы добавить свой канал - нужно быть подписанными на"
                                            f" {main_channel_name} и {check_chat_name}",
                                 parse_mode="Markdown", disable_web_page_preview=True, reply_markup=btn)
            # elif not check_chats(m.chat.id):
            #     btn = set_buttons(pattern='ready', **{'ready': "Подписался"})
            #     bot.send_message(m.chat.id, f"Чтобы добавить свой канал - нужно быть подписанными на"
            #                                 f" {main_channel_name} и {check_chat_name}",
            #                      parse_mode="Markdown", disable_web_page_preview=True, reply_markup=btn)
    elif target == 'notice':
        if len(m.text) < 101:
            if link:
                worker.channels[m.chat.id][link].notice = m.text
                btn = set_buttons(pattern='ready', **{'ready': 'Да notice 1', 'prev': 'Нет notice 0'})
                bot.send_message(m.chat.id, f"Сохраняем примечание?:\n"
                                            f"Примечание: {m.text}", reply_markup=btn)
            else:
                text = "Отправьте мне название вашего канала в формате @namechannel \n" \
                       "или ссылку на канал, если канал приватный."
                bot.send_message(m.chat.id, text, reply_markup=types.ReplyKeyboardRemove())
        else:
            bot.send_message(m.chat.id, "Слишком длинное примечание. Я не запомню.")
    elif target == 'ads_cost':
        if m.text.isdigit():
            worker.channels[m.chat.id][link].ads_cost = int(m.text)
            btn = set_buttons(pattern='ready', **{'ready': 'Верно ads_cost 1', 'prev': 'Назад ads_cost 0'})
            bot.send_message(m.chat.id, f"Сохраняем стоимость?:\n"
                                        f"Стоимость рекламы: {m.text}", reply_markup=btn)
        else:
            bot.send_message(m.chat.id, f"Вы ввели не число, а {m.text}")
    elif m.chat.username == admin and not worker.users[m.chat.id].target in ['admin', 'send_all', 'time_limit']:
        btn = set_buttons(pattern='admin')
        bot.send_message(m.chat.id, "Что будем делать?", reply_markup=btn)
        print(m)
    elif m.chat.username == admin and worker.users[m.chat.id].target == 'send_all':
        btn = set_buttons(pattern='admin', **{'Отправить всем': 'send all'})
        bot.send_message(m.chat.id, m.text, parse_mode='Markdown', reply_markup=btn)
    elif m.chat.username == admin and worker.users[m.chat.id].target == 'time_limit':
        if m.text.isdigit():
            btn = set_buttons(pattern='admin', **{'Сохранить': f'time limit {m.text}', "Не сохранять": f'time limit 0'})
            bot.send_message(m.chat.id, f'Медленный режим установлен на {m.text} часов', reply_markup=btn)
        else:
            bot.send_message(m.chat.id, 'Шутки шутишь?)')
    else:
        text = "Для того чтобы запустить объявление о продаже рекламы: \n" \
               "— Ваш личный  юзернейм должен быть в информации о канале;\n" \
               "— На канале должно быть более 1000 подписчиков. \n" \
               "Отправьте мне название вашего канала в формате @namechannel \n" \
               "или ссылку на канал, если канал приватный."
        print(f"USER {m.chat.username} WRITE ME SOMTHING")
        bot.send_message(m.chat.id, text, reply_markup=big_btn)


@bot.message_handler(func=lambda m: m.chat.id < 0 and m.chat.id not in [main_channel_id, check_chat_id]
                                    and worker.users.get(m.from_user.id),
                     content_types=['text', 'audio', 'document', 'photo', 'sticker', 'video', 'video_note',
                                    'voice', 'location', 'contact'])
def get_group_chat(m: types.Message):
    print(f"USER {m.from_user.username} YIELD IN CLOSED CHANNEL {worker.users[m.from_user.id]} =)")
    link = worker.users[m.from_user.id].target_url
    if link and worker.channels.get(m.from_user.id).get(link):
        text, btn = check_user_group(m.forward_from_chat.id, m.chat.id, link)
        bot.send_message(m.chat.id, text, reply_markup=btn, parse_mode='Markdown',
                         disable_web_page_preview=True)
        
        # try:
        #     print(f"USER {m.from_user.username} TRY PARSING DATA FROM CHANNEL {m.chat.title}")
        #     chat_ = bot.get_chat(m.chat.id)
        #     print(chat_)
        #     total = bot.get_chat_members_count(chat_.id)
        #     if total < 1000:
        #         bot.send_message(m.from_user.id, "В вашем канале меньше 1000 подписчиков.", reply_markup=big_btn)
        #         return
        #     if not worker.channels[m.from_user.id][link].subscribers:
        #         worker.channels[m.from_user.id][link].subscribers = total
        #     if not worker.channels[m.from_user.id][link].name:
        #         worker.channels[m.from_user.id][link].name = chat_.title
        #     if not worker.channels[m.from_user.id][link].chat_id:
        #         worker.channels[m.from_user.id][link].chat_id = chat_.id
        #     if not chat_.type == 'channel':
        #         worker.channels[m.from_user.id][link].chat_status = 'Группа'
        #     post = worker.channels[m.from_user.id][link].create_post(m.from_user.username)
        #     if chat_.description and m.from_user.username in chat_.description:
        #         print(f"USER {m.from_user.username} IN DESCRIPTION OF CHAT {chat_.title}")
        #         btn = set_buttons(pattern='edit')
        #         bot.send_message(m.from_user.id, post, parse_mode='Markdown', reply_markup=btn,
        #                          disable_web_page_preview=True)
        #     else:
        #         print(f"USER {m.chat.username} NOT IN DESCRIPTION OF CHAT {chat_.title}")
        #         for chat_member in bot.get_chat_administrators(m.chat.id):
        #             print(chat_member.user.username, "IS ADMIN")
        # 
        #             if chat_member.user.id == m.from_user.id:
        #                 btn = set_buttons(pattern='edit')
        #                 bot.send_message(m.from_user.id, post, parse_mode='Markdown', reply_markup=btn,
        #                                  disable_web_page_preview=True)
        #                 print()
        #                 break
        #             else:
        #                 print(chat_member.user.username, f' - админ чата {chat_.title}')
        #         else:
        #             print(f"USER {m.from_user.username} NOT IN CHAT {chat_.title} DISCRIPTION AND NOT IN ADMINS")
        #             worker.users[m.from_user.id].target = 'add_channel'
        #             btn = set_buttons(pattern='ready', **{'ready': f'Исправил add_channel {chat_.id}'})
        #             bot.send_message(m.from_user.id, f"Вы не являетесь администратором группы {chat_.title}, "
        #                                              f"нужно добавить свой @username в описание канала"
        #                                              "и нажать на кнопку, чтобы продолжить", reply_markup=btn)
        # 
        # except telebot.apihelper.ApiException:
        #     print(f"SLY USER {m.from_user.username} FORWARD MESSAGE BUT DON`T ADD IN CHANNEL")
        #     bot.send_message(m.from_user.id, "Так как это закрытый чат, необходимо добавить меня в этот канал, "
        #                                      "и написать там какое-нибудь сообщение.")
    else:
        bot.leave_chat(m.chat.id)


if __name__ == '__main__':
    counter = 0
    while True:
        try:
            bot.polling(none_stop=True, timeout=120)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ProxyError) as err:
            print(err)
            print("Тормозим бота")
            bot.stop_polling()
            time.sleep(1)
