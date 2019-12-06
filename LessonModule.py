from MySQLiter import MySQLiter
from settings import DB_CONNECTION_VALUES, THEME_OVER_TEXT

DB = MySQLiter(*DB_CONNECTION_VALUES)


class User:

    def __init__(self, user_id, **kwargs):
        user = DB.get_user(user_id, **kwargs)
        print("I'm in User __init__", user)
        for k, v in user.items():
            self.__setattr__(k, v)
        print(self)


def get_user(user_id, **kwargs):
    print(kwargs)
    user = User(user_id, **kwargs)


class Lesson:

    def __init__(self, text, voice=None, image=None):
        self.__text_lesson = text
        self.__voice = voice
        self.__image = image

    def __str__(self):
        return 'text: {0}, voice: {1}, image: {2}'.format(self.__text_lesson, self.__voice, self.__voice)

    @property
    def text(self):
        return self.__text_lesson

    def edit_text(self, other_text):
        self.__text_lesson = other_text

    @property
    def lesson_voice(self):
        return self.__voice

    def add_lesson_voice(self, voice):
        self.__voice = voice

    @property
    def lesson_image(self):
        return self.__image

    def add_lesson_image(self, image):
        self.__image = image


class Theme:

    def __init__(self, theme, user_id: User, add_new_theme=False):
        self.theme = theme
        self.__user_id = user_id
        self.__course = []
        self.__current_lesson = 0
        self.__course.append(Lesson(THEME_OVER_TEXT.format(self.theme)))
        if not add_new_theme:
            self.__course += get_thematical_course(self.theme)
        self.__lessons_count = len(self.__course)

    @property
    def current_lesson(self):
        return self.__current_lesson

    def __len__(self):
        return len(self.__course)

    def __has_next(self):
        self.__current_lesson += 1
        if self.__current_lesson < len(self.__course):
            return self.__current_lesson
        else:
            self.__course = self.__course[:1]
            return 0  # Theme is over

    def __has_prev(self):
        self.__current_lesson -= 1
        if 0 < self.__current_lesson < len(self.__course):
            return self.__current_lesson
        if len(self.__course) == 1:
            return 0
        return 1  # If current lesson out of range - return first lesson

    def get_first_lesson(self):
        self.__current_lesson = 1
        return self.__course[self.__current_lesson]

    def next_lesson(self):
        lesson_number = self.__has_next()
        return self.__course[lesson_number]

    def prev_lesson(self):
        lesson_number = self.__has_prev()
        return self.__course[lesson_number]

    def add_lesson(self, lesson):
        self.__course.append(lesson)

    def save(self):
        if self.__lessons_count < len(self.__course):
            DB.add_course(self.theme, self.__user_id, self.__course[self.__lessons_count])
            complete = 'Успешно добавлено {0} урок{1} в тему *{2}*'.format(
                len(self.__course) - self.__lessons_count,
                '' if len(self.__course) // 1 == 1 else '{0}'.format(
                    'а' if len(self.__course) // 1 in [2, 3, 4] else 'ов'),
                self.theme)
            return complete
        return 'Нет уроков для добавления в базу данных.'


def get_thematical_course(theme):
    _lessons = DB.get_course_by_theme(theme)
    course = []
    if _lessons:
        for _lesson in _lessons:
            course.append(
                Lesson(_lesson['text_lesson'], _lesson['voice_id'], _lesson['image_id']))
        return course
    return


def get_themes():
    themes = DB.return_all_themes()
    return themes


if __name__ == '__main__':
    print(get_themes())
