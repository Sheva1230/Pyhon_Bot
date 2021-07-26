import sqlite3


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