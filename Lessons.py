from MySQLiter import MySQLiter
from settings import DB_CONNECTION_VALUES

DB = MySQLiter(*DB_CONNECTION_VALUES)


class Lesson:

    def __init__(self, text, voice=None, image=None):
        self.__text_lesson = text
        self.__voice = voice
        self.__image = image

    @property
    def text(self):
        return self.__text_lesson

    @property
    def lesson_voice(self):
        return self.__voice

    @lesson_voice.setter
    def lesson_voice(self, voice):
        self.__voice = voice

    @property
    def lesson_image(self):
        return self.__image

    @lesson_image.setter
    def lesson_image(self, image):
        self.__image = image


class Theme:

    def __init__(self, theme):
        self.theme = theme
        self.course = {}

    def get_course(self):
        self.course = MySQLiter.get_course_by_theme(self.theme)



