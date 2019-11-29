import sqlite3

class SQLiterError(Exception): pass


class SQLiter:

    def __init__(self, database):
        self.db = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.db.cursor()

    def add_user(self, chat_id, **kwargs):
        sql_insert = 'INSERT INTO users ({0}) VALUES ({1})'
        if kwargs:
            list_tables = ['chat_id']
            list_values = [str(chat_id)]
            for k, v in kwargs.items():
                list_tables.append(str(k))
                if isinstance(v, str):
                    v = '\"{}\"'.format(v)
                list_values.append(str(v))
            sql_insert = sql_insert.format(', '.join(list_tables), ', '.join(list_values))
            print(sql_insert, "Cute")
            self.cursor.execute(sql_insert)
            self.db.commit()
            self.db.close()
        return 1

    def check_user(self, chat_id):
        sql_select_user = 'SELECT current_lesson FROM users WHERE chat_id={}'
        print(chat_id)
        some_user = self.cursor.execute(sql_select_user.format(chat_id)).fetchone()[0]
        if not some_user:
            return self.add_user(chat_id)
        return some_user

    def select_lesson(self, curr_lesson):

        with self.db:
            lesson = self.cursor.execute('SELECT * FROM lessons WHERE id = ?', (curr_lesson,)).fetchone()
            return lesson[1:]

    def set_user_next_id(self, table, column, query):
        sql_update = 'UPDATE {0} SET {1} = {2}'.format(table, column, query)
        with self.db:
            self.cursor.execute(sql_update)
            self.db.commit()

    def start_education(self, lesson_id):
        return self.cursor.execute(
            'SELECT theme_id, theme, text_lesson, next_lesson,'
            ' current_task, audio_id, image_id FROM lessons WHERE id =?', lesson_id).fetchone()
