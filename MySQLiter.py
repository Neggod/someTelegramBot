import pymysql
import pymysql.cursors
from settings import DB_CONNECTION_VALUES


class MySQLiter:
    '''
    TODO:
    Надо переопределить методы получения и сохранения уроков, получения и сохранения
    курса (в т.ч. если текущий урок не первый!!!), методы сохранения урока в табличке пользователей.
    обязательно запилить последний метод.
    '''

    def __init__(self, host, database, username, password):
        self.db = pymysql.connect(
            host=host,
            user=username,
            password=password,
            db=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cursor = self.db.cursor()

    def select_lesson(self, lesson_id):
        with self.db:
            self.cursor.execute('SELECT * FROM lessons WHERE lesson_id = %s)', lesson_id)
            return self.cursor.fetchone()

    def get_next_lesson(self, lesson_id):
        sql_insert = 'UPDATE lessons SET next_lesson_id = %s WHERE lesson_id = {0}'

    def max_lesson(self):
        sql_select = 'SELECT MAX(lesson_id) FROM lessons'
        with self.db:
            self.cursor.execute(sql_select)
            return self.cursor.fetchone()['MAX(lesson_id)']


    def select_lesson_by_user_id(self, user_id):
        with self.db:
            self.cursor.execute(
            'SELECT * FROM lessons WHERE lesson_id = ('
            'SELECT current_lesson FROM users WHERE user_id = %s)', user_id)
            return self.cursor.fetchone()

    def get_lessons_count_for_theme(self, theme_id):
        lessons = []
        count = 0
        with self.db:
            self.cursor.execute('SELECT lesson_id FROM lessons WHERE theme_id = %s', theme_id)
            for var in self.cursor.fetchall():
                lessons.append(var['lesson_id'])
            count = self.cursor.execute('SELECT COUNT(lesson_id) FROM lessons WHERE theme_id = %s', theme_id).fetchone()['COUNT(lesson_id)']
            return count, lessons

    def get_next_lesson_id(self, user_id):

        with self.db:
            self.cursor.execute(
                'SELECT next_lesson_id FROM lessons WHERE lesson_id = ('
                'SELECT current_lesson FROM users WHERE user_id = %s)', user_id)
            next_id = self.cursor.fetchone()['next_lesson_id']
        self.set_next_lesson(user_id, next_id)
        return

    def set_next_lesson(self, user_id, next_id=None):
        with self.db:
            if not next_id:
                next_id = self.get_next_lesson_id(user_id)
            self.cursor.execute(
                'UPDATE users SET current_lesson = {0} WHERE user_id = {1}'.format(next_id, user_id))
            self.db.commit()
            return next_id

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
            if not user:
                self.add_user(user_id, **kwargs)
                self.cursor.execute(sql_select, user_id)
                return self.cursor.fetchone()
            return user

    def add_lesson(self, **kwargs):
        columns = []
        values = []
        sql_insert = 'INSERT INTO lessons ({0}) VALUES ({1})'
        theme = kwargs['theme']
        for k, v in kwargs.items():
            if k == 'lesson_number':
                v == self.get_lesson_number_by_theme(theme)
                if v > 1:
                    v += 1
            if not v or k == 'new_lesson':
                continue
            v = '\'{}\''.format(v)
            columns.append(k)
            values.append(str(v))
        sql_insert = sql_insert.format(', '.join(columns), ', '.join(values))
        with self.db:
            print(sql_insert)
            self.cursor.execute(sql_insert)
            self.db.commit()

    def get_theme_id(self, theme=None):
        '''

        :param theme: exiting or new theme
        :return: return theme_id for theme or max id (if add new lesson)
        '''
        sql_select = 'SELECT MAX(theme_id) FROM lessons'
        if theme:
            sql_select += ' WHERE theme = \'{}\''.format(theme)
        with self.db:
            self.cursor.execute(sql_select)
            theme_id = self.cursor.fetchone()['MAX(theme_id)']
            print(theme_id, 1)
        if not theme_id:
            theme_id = self.get_theme_id()
            return theme_id + 1
        print(theme_id, 2)
        return theme_id

    def get_lesson_number_by_theme(self, theme=None):
        if not theme:
            return
        sql_select = 'SELECT lesson_number FROM lessons WHERE theme = \'{}\''.format(theme)
        with self.db:
            self.cursor.execute(sql_select)
            temp_number = self.cursor.fetchall()
        lesson_number = 1 #in database "1" - default lesson_number
        if not temp_number:
            return lesson_number
        for number in temp_number:
            if number['lesson_number'] > lesson_number:
                lesson_number = number['lesson_number']
        lesson_number += 1
        return lesson_number

    def get_course_by_theme(self, theme):
        '''
        From database get lesson_number:lesson_id, text_lesson, audio_id, image_id
        :param theme:
        :return: dict:
        '''
        pass


if __name__ == '__main__':
    test = MySQLiter(*DB_CONNECTION_VALUES)
    t = test.max_lesson()

    print(t)
