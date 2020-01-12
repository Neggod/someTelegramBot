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

db_name = parser.get('sqlite_db', 'name')
create_script = parser.get('sqlite_db', 'create_db')


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


class Channel:

    def __init__(self, link_channel, owner_id, name_channel=None, description=None,
                 subscribers=None, ads_cost=None, pr=None,
                 date_of_last_post=None, message_id=None, time_in_top_tape=None,
                 notice=None, chat_id=None, views_per_post=None, er=None, username=None):

        self.link_channel = link_channel
        self.name = name_channel
        self.description: list = description
        self.owner_id = owner_id
        self.subscribers = subscribers
        self.ads_cost = ads_cost
        self.pr = pr
        self.date_of_last_post = date_of_last_post
        self.message_id = message_id
        self.time_in_top_tape = time_in_top_tape
        self.notice = notice
        self.chat_id = chat_id
        self.views_per_post = views_per_post
        self.er = er
        self.post = None
        self.create_post(username)
        self.patterns = {'ads_cost': self.ads_cost, 'time': self.time_in_top_tape, 'notice': self.notice}

    def get_link(self):
        if self.link_channel.startswith("@"):
            return self.link_channel
        elif self.name:
            return f"[@{self.name}]({self.link_channel})"
        else:
            return self.link_channel

    def create_post(self, username):
        temp_name = None
        print(self.name)
        if self.link_channel.count("_") and self.link_channel.startswith("@"):
            link_channel = self.link_channel.replace("_", "\_")
        else:
            link_channel = self.link_channel
        if self.name:
            self.name.replace("_", "\_")
            temp_name = ("[" + self.name + "](" + link_channel + ")")
        print(self.name)
        self.post = u'*Канал*: {0}\nТематика: {1}\n\n\U0001F465 Подписчиков: {2}\n'.format(
            (link_channel if link_channel.startswith("@") else f'{temp_name if temp_name else ""}'),

            (self.description if self.description else ""),
            self.subscribers)

        if self.views_per_post:
            self.post += u'👁 Просмотров на пост: {}\n'.format(self.views_per_post)  # \ud83d\udc41 looks
        if self.er:
            self.post += u"📊 ER: {}\n".format(self.er)  # \ud83d\udcca ER
        if self.ads_cost:
            self.post += u"💵 Стоимость рекламы: {} рублей\n".format(self.ads_cost)  # \ud83d\udcb5 cost
        if self.time_in_top_tape:
            self.post += u"⏰ Время Топ/Лента: {}\n".format(self.time_in_top_tape)
        if self.pr or self.pr == 0:
            self.post += u"♻ Взаимопиар: {}\n".format('Да' if self.pr else 'Нет')
        if self.notice:
            self.post += u"\U0001F4DD Примечание: {}\n".format(self.notice)

        self.post += u"😎 Админ: @{0}".format(username.replace("_", "\_"))  # \ud83d\ude0e
        print(self.post)
        return self.post


class WorkerError(Exception):
    pass


class Worker:

    def __init__(self, time_limit):
        self.db = SQLiter(os.path.join(BASE_DIR, db_name))
        self.users = {}
        self.channels = defaultdict(dict)
        self.__time_limit = time_limit

    @property
    def limit(self):
        return self.__time_limit
    @limit.setter
    def limit(self, other):
        self.__time_limit = int(other)

    def _get_channel_from_db(self, link):
        return self.db.get_channel(link)

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

    def create_new_channel(self, link, owner_id, username=None):
        print(link, "STARTING CREATE NEW CHANNEL")
        if link.startswith("@") or link.startswith("https://t.me/joinchat/"):
            print("START PARSING")
            result = self.parse_link(link)
            if result and result[0]:
                print(result)
                name, names = result

                if name:

                    self.channels[owner_id][link] = Channel(link, owner_id, name_channel=name,
                                                            username=username)
                if names:
                    self.channels[owner_id][link].subscribers = int(names['Подписчиков'].replace("'", ""))
                    print(f'ПОДПИСЧИКОВ - {self.channels[owner_id][link].subscribers}')
                    self.channels[owner_id][link].views_per_post = names["Просмотров на пост"]
                    self.channels[owner_id][link].er = names['ER'] if names['ER'] != '%' else None
                print(f'SUCCESSFUL PARSING {link}')

                return 1
            else:
                self.channels[owner_id][link] = Channel(link, owner_id, username=username)
                return 2
        else:
            raise WorkerError("Something wrong ad 138")

    def check_channel(self, link, owner_id, username=None):
        # "id"	"owner_id"	"chat_id"	"link_channel"	"name_channel"	"description"	"subscribers"
        # "views_per_post"	"er"	"ads_cost"	"time_in_top_tape"	"pr"
        # "notice"	"date_of_last_post"	"message_id"

        if self.channels.get(owner_id) and self.channels[owner_id].get(link):
            if self.channels[owner_id][link].date_of_last_post:
                time_ = datetime.datetime.fromtimestamp(self.channels[owner_id][link].date_of_last_post)
                now = datetime.datetime.now()
                if (now - time_) // (60 * 60) >= self.__time_limit:
                    name, names = self.parse_link(link)
                    if name and not name == self.channels[owner_id][link].name_channel:
                        self.channels[owner_id][link].name_channel = name
                    if names:
                        self.channels[owner_id][link].subscribers = int(names['Подписчиков'].replace("'", ""))
                        print(f'ПОДПИСЧИКОВ - {self.channels[owner_id][link].subscribers}')
                        self.channels[owner_id][link].views_per_post = names["Просмотров на пост"]
                        self.channels[owner_id][link].er = names['ER'] if names['ER'] != '%' else None
                    print(f'SUCCESSFUL PARSING {link}')
           
            return 0

        vals = self._get_channel_from_db(link)

        if vals:
            print(f"CHAT {link} BY {owner_id} IN DB")
            self.channels[owner_id][link] = Channel(link, owner_id, name_channel=vals[4],
                                                    description=vals[5], subscribers=vals[6],
                                                    ads_cost=vals[9],
                                                    pr=vals[11], date_of_last_post=vals[13], message_id=vals[14],
                                                    time_in_top_tape=vals[10], notice=vals[12], chat_id=vals[2],
                                                    views_per_post=vals[7], er=vals[8], username=username)

            time_ = datetime.datetime.fromtimestamp(self.channels[owner_id][link].date_of_last_post)
            now = datetime.datetime.now()
            if (now - time_) // (60 * 60) >= self.__time_limit:
                name, names = self.parse_link(link)
                if name and not name == self.channels[owner_id][link].name_channel:

                    self.channels[owner_id][link].name_channel = name
                if names:
                    self.channels[owner_id][link].subscribers = int(names['Подписчиков'].replace("'", ""))
                    print(f'ПОДПИСЧИКОВ - {self.channels[owner_id][link].subscribers}')
                    self.channels[owner_id][link].views_per_post = names["Просмотров на пост"]
                    self.channels[owner_id][link].er = names['ER'] if names['ER'] != '%' else None
                print(f'SUCCESSFUL PARSING {link}')
            return 0
        else:
            return self.create_new_channel(link, owner_id, username)

    def set_limit(self, value):
        if value.isdigit():
            self.__time_limit = int(value)
            parser.set('Telegram', 'time_limit', value)
            with open(cfg_name, 'w', encoding="UTF-8") as fh:
                parser.write(fh)

        else:
            raise WorkerError("at line 163")

    def check_timer(self, chat_id, link, now):
        print(chat_id, link)
        if self.channels.get(chat_id) and self.channels[chat_id].get(link):
            status = self.check_channel(link, chat_id)
            # now = datetime.datetime.now()
            if status == 0 and self.channels[chat_id][link].date_of_last_post:
                print("CHECK LAST TIME SENDING")
                delta = now - datetime.datetime.fromtimestamp(self.channels[chat_id][link].date_of_last_post)
                if delta.seconds // (60 * 60 * self.__time_limit):
                    print("TIME OK")
                    self.channels[chat_id][link].date_of_last_post = int(now.timestamp())
                    return True
                else:
                    print("TIME NOT OK")
                    return False
            elif not self.channels[chat_id][link].date_of_last_post:
                print("NOT TIME")
                self.channels[chat_id][link].date_of_last_post = int(now.timestamp())
                return True
            else:
                print("STATUS NOT OK, TIME NOT KNOWN")
                return False
        else:
            print("NOT USER OR CHANNEL IN MEMO")
            return False

    def all_users(self):
        return self.db.get_all_users()

    def save_data_channel(self, chat_id, link):
        if self.channels.get(chat_id) and self.channels.get(chat_id).get(link):
            channel = self.channels[chat_id][link]
            self.db.add_new_channel(channel.name, channel.link_channel, channel.description,
                                    channel.owner_id,
                                    channel.subscribers, channel.ads_cost, channel.time_in_top_tape, channel.pr,
                                    channel.date_of_last_post, channel.message_id, channel.notice, channel.chat_id,
                                    channel.views_per_post, channel.er)

    @staticmethod
    def parse_link(link):
        def login(session):
            print("TELEMETR START AUTH")
            login = parser.get('Telemetr', 'login')
            password = parser.get('Telemetr', 'password')
            login_url = parser.get('Telemetr', 'login_url')
            payload = {'login[email]': login, 'login[password]': password, 'do_login': ''}
            try:
                resp = session.post(login_url, data=payload)
                session.headers['Cookie'] = 'hash=' + session.cookies['hash']
                parser.set('Telemetr-headers', 'Cookie', session.headers['Cookie'])
                with open(cfg_name, 'w') as f:
                    parser.write(f)
                    time.sleep(1)
                print("TELEMETR AUTH. COOKIE - SAVED")
                return session
            except (requests.exceptions.ReadTimeout, requests.exceptions.ProxyError) as e:
                print(e)
                return

        session = requests.Session()
        for k, v in parser['Telemetr-headers'].items():
            if k == "Cookie" and not v:
                continue
            session.headers[k] = v
        if not session.headers.get('Cookie'):
            session = login(session)
        if not session:
            return
        elif session:
            print(f"START PARSING {link}")
            datas = {'name': link}
            stat_link = parser.get('Telemetr', 'statistic_url')
            try:
                new_resp = session.get(stat_link, params=datas)
                print("PARSING DONE, LINK GET")
                soup = bs(new_resp.content.decode(encoding="UTF-8"), 'lxml')
                cols = soup.find_all('div', attrs={"class": "col-lg-4 col-md-4"})
                if cols:
                    print(f"HAS CHANNEL {link} IN TELEMETR")
                    names = dict.fromkeys(["Подписчиков", "Просмотров на пост", "ER"], "TEXT")
                    name = cols[0].find('a', attrs={"class": 'kt-widget__username'}).text.strip()
                    categories = []

                    for col in cols[1:]:
                        for wid in col.find_all('div', attrs={'class': 'kt-widget4__item'}):
                            name_ = wid.find('span', attrs={"class": 'kt-widget4__title'})

                            if not name_ or not names.get(name_.text.strip(), 0):
                                continue
                            name_ = name_.text.strip()
                            names[name_] = wid.find('span', attrs={"class": 'kt-number kt-font-brand'}).text.strip()

                    if name and names['Подписчиков']:
                        print(f"LUCKY PARSING {link}")
                        return name, names
                    else:
                        print(f"UNLUCKY PARSING {link}")
                        return None
                else:
                    print(f"HASN`T CHANNEL {link} IN TELEMETR")
                    return None
            except (requests.exceptions.ReadTimeout, requests.exceptions.ProxyError) as e:
                print(e)
                print("PARSING DOESN`T WORK")
                return
        else:
            print("SOMETHING ERROR IN PARSING")
            return None
