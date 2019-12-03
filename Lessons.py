from MySQLiter import MySQLiter
from settings import DB_CONNECTION_VALUES, THEME_OVER_TEXT

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
        self.course = []
        self.current_lesson = 1  # First lesson in course. 0 - for theme over text
        self.course.append(Lesson(THEME_OVER_TEXT.format(self.theme)))

    def get_course(self):
        _lessons = MySQLiter.get_course_by_theme(self.theme)
        for lesson in _lessons:
            self.course.insert(lesson['lesson_number'],
                               Lesson(lesson['text_lesson'], lesson['audio_id'], lesson['image_id']))

    def add_course(self):
        """
        Commit current object.
        :return:
        """
        if len(self.course) > 1:
            DB.add_course(self)

    def add_lesson(self, ):
