import pymysql
import pymysql.cursors
from settings import DB_CONNECTION_VALUES, ADMINS_ID


class MySQLiter:
    '''
    TODO:
    Надо переопределить методы получения и сохранения уроков, получения и сохранения
    курса (в т.ч. если текущий урок не первый!!!), методы сохранения урока в табличке пользователей.
    обязательно запилить последний метод.
    '''

    def __check_tables(self):
        lessons = """CREATE TABLE IF NOT EXISTS `lessons` (
      `lesson_id` int(11) NOT NULL AUTO_INCREMENT,
      `theme_id` int(11) DEFAULT NULL,
      `theme` tinytext,
      `lesson_number` int(11) NOT NULL DEFAULT '1',
      `text_lesson` text NOT NULL,
      `current_task` int(11) DEFAULT NULL,
      `next_lesson_id` int(11) DEFAULT NULL,
      `audio_id` tinytext,
      `image_id` tinytext,
      PRIMARY KEY (`lesson_id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"""
        users = """CREATE TABLE IF NOT EXISTS `users` (
      `user_id` int(11) NOT NULL,
      `first_name` tinytext,
      `current_theme` int(11) DEFAULT '1',
      `current_task` tinyint(4) DEFAULT '1',
      `email` tinytext,
      PRIMARY KEY (`user_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

"""
        with self.db:
            self.cursor.execute(lessons)
            self.cursor.execute(users)
            self.db.commit()

    def __init__(self, host, database, username, password):
        self.db = pymysql.connect(
            host=host,
            user=username,
            password=password,
            db=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cursor = self.db.cursor()
        self.__check_tables()

    def add_user(self, user_id, **kwargs):
        sql_insert = 'INSERT INTO users ({0}) VALUES ({1})'
        list_tables = ['user_id']
        list_values = [str(user_id)]
        if kwargs:
            for k, v in kwargs.items():
                list_tables.append(str(k))
                if isinstance(v, str):
                    v = '\"{}\"'.format(v)
                list_values.append(str(v))
        sql_insert = sql_insert.format(', '.join(list_tables), ', '.join(list_values))
        with self.db:
            self.cursor.execute(sql_insert)
            self.db.commit()
        print('Добавлен новый усер')

    def get_user(self, user_id, **kwargs):
        sql_select = 'SELECT * FROM users WHERE user_id = %s'
        with self.db:
            self.cursor.execute(sql_select, user_id)
            user = self.cursor.fetchone()
            print("I'm in db get user=)", user)
            if not user:
                self.add_user(user_id, **kwargs)
                self.cursor.execute(sql_select, user_id)
                return self.cursor.fetchone()
            return user

    def return_all_themes(self):
        sql_request = 'SELECT theme FROM lessons'
        themes = []
        with self.db:
            self.cursor.execute(sql_request)
            pool = self.cursor.fetchall()
        for theme in pool:
            if theme['theme'] in themes:
                continue
            themes.append(theme['theme'])
        return themes

    def get_theme_id(self, theme):
        '''

        :param theme: exiting or new theme
        :return: return theme_id for theme or max id (if add new lesson)
        '''
        sql_select = 'SELECT theme_id FROM lessons WHERE theme LIKE  "%{0}%"'.format(theme)
        with self.db:
            self.cursor.execute(sql_select)
            theme_id = self.cursor.fetchone()
            if not theme_id:
                self.cursor.execute('SELECT MAX(theme_id) FROM lessons')
                theme_id = self.cursor.fetchone()
                return theme_id['MAX(theme_id)'] + 1
            return theme_id['theme_id']

    def get_course_by_theme(self, theme):
        '''
        From database get lesson_number: text_lesson, audio_id, image_id
        :param theme:
        :return: dict:
        '''
        theme = '"{0}"'.format(theme)
        # theme_id = self.__get_theme_id_from_users(user_id)
        sql_request = 'SELECT text_lesson, voice_id, image_id FROM lessons WHERE theme = {0}'.format(theme)
        with self.db:
            self.cursor.execute(sql_request)
            return self.cursor.fetchall()

    def set_current_theme(self, theme, user_id):
        """
        
        :param theme: 
        :param user_id: 
        :return: 
        """
        theme_id = self.get_theme_id(theme)
        sql_request = "UPDATE users SET current_theme = {0} WHERE user_id = {1}".format(theme_id, user_id)
        with self.db:
            self.cursor.execute(sql_request)
            self.db.commit()

    def add_course(self, theme, user_id, course_list):
        """
        Insert into database course params
        :param theme:
        :param user_id:
        :param course_list:
        :return: True or False
        """
        if user_id in ADMINS_ID:
            sql_request = 'INSERT theme, theme_id, text_lesson, voice_id, image_id INTO lessons VALUES {0}'
            values = []
            theme_id = self.get_theme_id(theme)
            for _lesson in course_list:
                value = (theme, theme_id, _lesson.text, _lesson.voice, _lesson.image)
                values.append(value)
            sql_request.format(tuple(values))
            with self.db:
                self.cursor.execute(sql_request)
                self.db.commit()

    def __get_theme_id_from_users(self, user_id):
        sql_request = "SELECT current_theme FROM users WHERE user_id = {0}".format(user_id)
        with self.db:
            self.cursor.execute(sql_request)
            theme_id = self.cursor.fetchone()['current_theme']
            return theme_id


if __name__ == '__main__':
    test = MySQLiter(*DB_CONNECTION_VALUES)
    f = test.return_all_themes()
    print(f)
    id1 = test.get_theme_id(f[1])
    id2 = test.get_theme_id('Foo')
    print(id1, id2)
