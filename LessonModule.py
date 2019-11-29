from MySQLiter import MySQLiter
from settings import DB_CONNECTION_VALUES

DB = MySQLiter(*DB_CONNECTION_VALUES)


class User:

    def __init__(self, user_id, **kwargs):
        self.user = DB.get_user(user_id, **kwargs)
        for k, v in self.user:
            self.__setattr__(k, v)

    def set_next_lesson(self, user_id):
        self.user['current_lesson'] = DB.set_next_lesson(user_id)


def get_user(user_id, **kwargs):
    user = User(user_id, **kwargs)
    return user.user['current_lesson']

class Task:
    pass


'''class Lesson:

    def __init__(self, user_id):
        self.lesson = DB.select_lesson(user_id)

    def get_next_lesson(self, user_id):
        next_lesson = DB.get_next_lesson_id(user_id)
        if next_lesson:
            return DB.select_lesson(next_lesson)
        return 'На этом пока всё. Увидимся позже. Спасибо'
        '''


def has_next_lesson(user_id):
    if not DB.get_next_lesson_id(user_id):
        return False
    return True


class Lesson:

    def __init__(self, theme_id=None, theme=None, lesson_number=None, text_lesson=None,
                 next_id=None, audio_id=None, image_id=None, lesson_id=None, user_id=None, new_lesson=False):
        self.lesson_id = lesson_id
        self.theme_id = theme_id
        self.theme = theme
        self.lesson_number = lesson_number
        self.text_lesson = text_lesson
        self.next_lesson = next_id
        self.audio_id = audio_id
        self.image_id = image_id
        self.current_task = None
        self.new_lesson = new_lesson
        if not new_lesson and user_id:
            self.get_lesson_from_db_by_chat_id(user_id)

    def get_lesson_from_db_by_chat_id(self, user_id):
        current_lesson = DB.select_lesson_by_user_id(user_id)
        if current_lesson:
            for k, v in current_lesson.items():
                self.__setattr__(k, v)

    def set_lesson_item(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def add_lesson(self):
        self.theme_id = DB.get_theme_id(self.theme)
        self.lesson_number = DB.get_lesson_number_by_theme(self.theme)
        if self.new_lesson:
            DB.add_lesson(**self.__dict__)

    def get_next_lesson(self, user_id):
        next_lesson = DB.get_next_lesson_id(user_id)
        if next_lesson:
            self.set_lesson_item(next_lesson)
        else:
            self.text_lesson = 'На этом пока всё. Увидимся позже. Спасибо'

    def clear(self, new_lesson=None):
        for k in self.__dict__:
            self.__setattr__(k, None)
        if new_lesson:
            self.new_lesson = True
        print(self.__dict__)


class Lesson1:

    def __init__(self, text_lesson, audio_id=None, image_id=None):
        self.lesson_id = None
        self.text_lesson = text_lesson
        self.audio_id = audio_id
        self.image_id = image_id

    @property
    def get_Lesson(self):
        lesson_parts = {'text_lesson': self.text_lesson, 'audio_id': self.audio_id, 'image_id': self.image_id}
        return lesson_parts


class Theme(Lesson1):
    pass


if __name__ == '__main__':

    lesson = Lesson(user_id=123)
    lesson.clear()

