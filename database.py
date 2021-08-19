import sqlite3
import random
from typing import Dict


class DefaultType:
    """ Изпользуется для преобразования типов полей

        Также гарантирует возврат поля того типа, который был передан
     """

    def __init__(self, obj_type, value):
        self.type = obj_type
        self.value = value


class DefaultTypes:
    """ Перечисление стандартных типов, использумых в классе Database """

    STR = DefaultType(str, "")  # Используется, если не был передан другой тип
    INT = DefaultType(int, 0)
    FLOAT = DefaultType(float, 0.0)
    BOOL = DefaultType(bool, False)


class Setting:
    """ Настройка сервера """

    def __init__(self, _name, _value, data_class, description: str, admin_level=0):
        self.name = _name
        self.value = _value
        self.dataclass = data_class
        self.description = description
        self.admin_level = admin_level


class Database:
    """ Класс, отвечающий за работу с базой данных

        Поле - это строка, в которой хранятся разлиные данные пользователя.
        Полей может быть нограниченнок кол-во

        Пример записи полей в БД: fields="warnings=10&other_data=100&"

        Поля разделены между собой символом '&'


        DefaultValues исользуется для преобразования значения из строки в нужный тип данных или
        возвращение default значения если у пользователя отсутствует нужное поле

    """

    def __init__(self):
        # Стандартные настройки
        self.available_chat_settings: Dict[str, Setting] = {"set_1": Setting("set_1", 0, int, "Нету"),
                                                            "set_2": Setting("set_2", 0, int, "Нету"),
                                                            "set_3": Setting("set_3", 0, int, "Нету"),
                                                            "set_4": Setting("set_4", 0, int, "Нету"),
                                                            "set_5": Setting("set_5", 0, int, "Нету"),}
        self.default_chat_settings = ""

        # Генерируем стандартную настройку для новых чатов
        for setting_name in self.available_chat_settings:
            setting = self.available_chat_settings[setting_name]
            self.default_chat_settings += f"{setting.name}={setting.value}&"

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("CREATE TABLE IF NOT EXISTS chats_settings (chat_id INT, settings)")
            sql.execute("CREATE TABLE IF NOT EXISTS chats (chat_id INT, user_id INT, fields)")
            sql.execute("CREATE TABLE IF NOT EXISTS library (library_name, custom_names, description, books, hrefs, "
                        "random_id)")

    @staticmethod
    def get_user(chat_id, user_id):
        """ Полуить пользователя из базы данных (или создать и получить) """

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM chats WHERE chat_id=? and user_id=?", (chat_id, user_id))
            user = sql.fetchone()
            if user is not None:
                return user

            sql.execute("INSERT INTO chats VALUES (?, ?, ?)", (chat_id, user_id, ""))
            return [chat_id, user_id, ""]

    def add_chat(self, chat_id):
        """ Добавить новый чат """

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM chats_settings WHERE chat_id=?", (chat_id,))
            if sql.fetchone() is not None:
                return

            sql.execute("INSERT INTO chats_settings VALUES (?, ?)", (chat_id, self.default_chat_settings))

    def set_chat_setting(self, chat_id, setting_name, setting_value, admin_level=0) -> bool:
        """ Установить настройку беседы """

        if setting_name not in self.available_chat_settings:
            return False
        if self.available_chat_settings[setting_name].admin_level > admin_level:
            pass

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT settings FROM chats_settings WHERE chat_id=?", (chat_id,))
            settings = sql.fetchone()[0]

            try:
                self.available_chat_settings[setting_name].dataclass(setting_value)
            except Exception as ex:
                print(ex)
                return False

            settings = self.__set_field(settings, setting_name, setting_value)
            sql.execute("UPDATE chats_settings SET settings=? WHERE chat_id=?", (settings, chat_id))

            return True

    def get_chat_setting(self, chat_id, setting_name, admin_level=0):
        """ Получить настройку беседы """

        if setting_name not in self.available_chat_settings:
            return False

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT settings FROM chats_settings WHERE chat_id=?", (chat_id,))
            settings = sql.fetchone()[0]

            value = self.available_chat_settings[setting_name].dataclass(self.__get_from_field(settings, setting_name))

            return value

    @staticmethod
    def __get_from_field(field, field_name):
        """ Получить значение поля из строки полей """

        field = field.split("&")
        for f in field:
            if f.split("=")[0] == field_name:
                return f.split("=")[1]
        return None

    @staticmethod
    def __set_field(fields, field_name, value):
        """ Установить значение поля в строке полей """

        if f"{field_name}=" in fields:
            return fields.replace(f"{field_name}={Database.__get_from_field(fields, field_name)}",
                                  f"{field_name}={value}")
        return fields + f"{field_name}={value}&"

    def get_field(self, chat_id, user_id, field_name, default_type: DefaultType = DefaultTypes.STR):
        """ Получить значение поля определенного пользователя """

        user = self.get_user(chat_id, user_id)
        value = self.__get_from_field(user[2], field_name)

        if default_type is not None and value is not None:
            value = default_type.type(value)

        return value if value is not None else (default_type.value if default_type is not None else None)

    def set_field(self, chat_id, user_id, field_name, value):
        """ Установить значение поля определенного пользователя """

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            user = self.get_user(chat_id, user_id)
            fields = self.__set_field(user[2], field_name, value)
            sql.execute("UPDATE chats SET fields=? WHERE chat_id=? and user_id=?", (fields, chat_id, user_id))

    @staticmethod
    def new_library(library_name) -> bool:
        """ Добавление новой библиотеки """

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT * FROM library WHERE library_name=?", (library_name,))

            if sql.fetchone():
                return False

            random_id = str(random.randint(0, 999))

            sql.execute("INSERT INTO library VALUES (?, ?, ?, ?, ?, ?)", (library_name, "", "", "", "", random_id))

            return True

    def get_library_name(self, library_name):
        """ Получить имя библиотеки """

        library_name = library_name.lower()
        libraries = self.get_all_library_names()

        for library in libraries:
            if library[0].lower() == library_name:
                return library[0]

            for _lib_name in library[1]:
                if _lib_name.lower() == library_name:
                    return library[0]

        return None

    def get_library(self, library_name) -> list:
        """ Получить библиотеку

            Возвращает [описание, книги, ссылки]
         """

        library_name = self.get_library_name(library_name)
        print(library_name)
        if library_name is None:
            return []

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT * FROM library WHERE library_name=?", (library_name,))

            library = sql.fetchone()

            books = [book.split("  ") for book in library[3].split("&") if len(book)]
            hrefs = [href.split("  ") for href in library[4].split("&") if len(href)]

            # print(library)

            return [library[2], books, hrefs]

    @staticmethod
    def get_all_library_names() -> list:
        """ Получить все имена всех библиотек """

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT * FROM library")

            return [[library[0], library[1].split("&")] for library in sql.fetchall()]

    def add_library_href(self, library_name, href, description) -> bool:
        """ Добавить библиотеке ссылку """

        library_name = self.get_library_name(library_name)
        if library_name is None:
            return False

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT hrefs FROM library WHERE library_name=?", (library_name,))

            l_hrefs = sql.fetchone()[0]
            if href in l_hrefs:
                return False
            l_hrefs += f"{href}  {description}&"

            sql.execute("UPDATE library SET hrefs=? WHERE library_name=?", (l_hrefs, library_name))

        return True

    def del_library_href(self, library_name, href) -> bool:
        """ Удалить ссылку у библиотеки """

        library_name = self.get_library_name(library_name)
        if library_name is None:
            return False

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT hrefs FROM library WHERE library_name=?", (library_name,))

            l_hrefs = sql.fetchone()[0]
            if href in l_hrefs:
                for hr in l_hrefs.split("&"):
                    if href in hr:
                        l_hrefs = l_hrefs.replace(f"{hr}&", "")
                        break
            else:
                return False

            sql.execute("UPDATE library SET hrefs=? WHERE library_name=?", (l_hrefs, library_name))

        return True

    def add_library_book(self, library_name, name, author, description):
        """ Добавить книгу библиотеке """

        library_name = self.get_library_name(library_name)
        if library_name is None:
            return False

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT hrefs FROM library WHERE library_name=?", (library_name,))

            l_books = sql.fetchone()[0]
            if name in l_books:
                return False
            l_books += f"{name}  {author}  {description}&"

            sql.execute("UPDATE library SET books=? WHERE library_name=?", (l_books, library_name))

            return True

    def del_library_book(self, library_name, book) -> bool:
        """ Удалить книгу у библиотеки """

        library_name = self.get_library_name(library_name)
        if library_name is None:
            return False

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT books FROM library WHERE library_name=?", (library_name,))

            l_books = sql.fetchone()[0]
            if book in l_books:
                for bk in l_books.split("&"):
                    if book in bk:
                        l_books = l_books.replace(f"{bk}&", "")
                        break
            else:
                return False

            sql.execute("UPDATE library SET books=? WHERE library_name=?", (l_books, library_name))

        return True

    def set_library_description(self, library_name, description) -> bool:
        """ Установить описание библиотеки """

        library_name = self.get_library_name(library_name)
        if library_name is None:
            return False

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("UPDATE library SET description=? WHERE library_name=?", (description, library_name))

        return True
