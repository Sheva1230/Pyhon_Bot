import sqlite3
import re


class DefaultType():
    """ Изпользуется для преобразования типов полей

        Также гарантирует возврат поля того типа, который был передан
     """

    def __init__(self, type, value):
        self.type = type
        self.value = value


class DefaultTypes:
    """ Перечисление стандартных типов, использумых в классе Database """

    STR = DefaultType(str, "")  # Используется, если не был передан другой тип
    INT = DefaultType(int, 0)
    FLOAT = DefaultType(float, 0.0)
    BOOL = DefaultType(bool, False)


class Database:
    """ Класс, отыечающий за работу с базой данных

        Поле - это строка, в которой хранятся разлиные данные пользователя.
        Полей может быть нограниченнок кол-во

        Пример записи полей в БД: fields="warnings=10&other_data=100&"

        Поля разделены между собой символом '&'


        DefaultValues исользуется для преобразования значения из строки в нужный тип данных или
        возвращение default значения если у пользователя отсутствует нужное поле

    """

    def __init__(self):
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("CREATE TABLE IF NOT EXISTS chats (chat_id INT, user_id INT, fields)")
            sql.execute("CREATE TABLE IF NOT EXISTS library (library_name, custom_names, description, books, hrefs)")

    def get_user(self, chat_id, user_id):
        """ Полуить пользователя из базы данных (или создать и получить) """

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM chats WHERE chat_id=? and user_id=?", (chat_id, user_id))
            user = sql.fetchone()
            if user is not None:
                return user

            sql.execute("INSERT INTO chats VALUES (?, ?, ?)", (chat_id, user_id, ""))
            return [chat_id, user_id, ""]

    def _get_from_field(self, field, field_name):
        """ Получить значение поля из строки полей """

        field = field.split("&")
        for f in field:
            if f.split("=")[0] == field_name:
                return f.split("=")[1]
        return None

    def get_field(self, chat_id, user_id, field_name, default_type: DefaultType=DefaultTypes.STR):
        """ Получить значение поля определенного пользователя """

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            user = self.get_user(chat_id, user_id)
            value = self._get_from_field(user[2], field_name)

            if default_type is not None and value is not None:
                value = default_type.type(value)

            return value if value is not None else (default_type.value if default_type is not None else None)

    def _set_field(self, fields, field_name, value):
        """ Установить значение поля в строке полей """

        if f"{field_name}=" in fields:
            return fields.replace(f"{field_name}={self._get_from_field(fields, field_name)}", f"{field_name}={value}")
        return fields + f"{field_name}={value}&"

    def set_field(self, chat_id, user_id, field_name, value):
        """ Установить значение поля определенного пользователя """

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            user = self.get_user(chat_id, user_id)
            fields = self._set_field(user[2], field_name, value)
            sql.execute("UPDATE chats SET fields=? WHERE chat_id=? and user_id=?", (fields, chat_id, user_id))

    def new_library(self, library_name) -> bool:
        """ Добавление новой библиотеки """

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT * FROM library WHERE library_name=?", (library_name,))

            if sql.fetchone():
                return False

            sql.execute("INSERT INTO library VALUES (?, ?, ?, ?, ?)", (library_name, "", "", "", ""))

            return True

    def get_library_name(self, library_name):
        """ Получить имя библиотеки """

        library_name = library_name.lower()
        librarys = self.get_all_library_names()

        for library in librarys:
            if library[0] == library_name:
                return library[0]

            for _lib_name in library[1]:
                if _lib_name == library_name:
                    return library[0]

            return None

    def get_library(self, library_name) -> list:
        """ Получить библиотеку

            Возвращает [описание, книги, ссылки]
         """

        library_name = self.get_library_name(library_name)
        if library_name is None:
            return False

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT * FROM library WHERE library_name=?", (library_name,))

            library = sql.fetchone()

            books = library[3]
            hrefs = [href.split("  ") for href in library[4].split("&") if len(href)]

            # print(hrefs)

            return [library[2].capitalize(), books, hrefs]

    def get_all_library_names(self) -> list:
        """ Получить все имена всех библиотек """

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT * FROM library")

            return [[library[0], library[1].split("&")] for library in sql.fetchall()]

    def add_library_href(self, library_name, href, descripion) -> bool:
        """ Добавить библиотеке ссылку """

        library_name = self.get_library_name(library_name)
        if library_name is None:
            return False

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT hrefs FROM library WHERE library_name=?", (library_name,))

            l_hrefs = sql.fetchone()[0]
            l_hrefs += f"{href}  {descripion}&"

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

    def set_library_description(self, library_name, description) -> bool:
        """ Установить описание библиотеки """

        library_name = self.get_library_name(library_name)
        if library_name is None:
            return False

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("UPDATE library SET description=? WHERE library_name=?", (description, library_name))

        return True