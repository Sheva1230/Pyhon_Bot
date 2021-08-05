import json
import os

from AI import AI, Command
from database import Database, DefaultTypes
from vkbottle.bot import Bot, Message


class VkBot(Bot):  # Класс бота
    def __init__(self):
        with open("config.json") as file:
            self.config = json.load(file)
            self.database = Database()

            self.commands = {}

            super().__init__(token=self.config["access_token"])

    def add_warning_msg(self, message: Message):  # Добавление пред. пользователю через объект Message
        self.add_warning(message.chat_id, message.from_id)

    def add_warning(self, chat_id, user_id):  # Добавление пред. пользователю через id чата и пользователя
        warnings = self.database.get_field(chat_id, user_id, "warnings", DefaultTypes.INT)

        if warnings is None:
            return

        self.database.set_field(chat_id, user_id, "warnings", warnings + 1)

    def get_warnings_msg(self, message: Message):  # Получить пред. пользователя через объект Message
        return self.get_warnings(message.chat_id, message.from_id)

    def get_warnings(self, chat_id, user_id):  # Получить пред. пользователю через id чата и пользователя
        return self.database.get_field(chat_id, user_id, "warnings", DefaultTypes.INT)

    def command(self, aliases: list = None, description: str = "Нету", big_desc: str = "Нету"):  # Декоратор для комманд
        def dec(func):
            self.commands[func.__name__] = [func, description, big_desc, aliases]
            if aliases is not None:
                for name in aliases:
                    self.commands[f"${name}"] = self.commands[func.__name__]
            return func
        return dec

    async def call_command(self, message: Message, command: Command):   # Вызов комманды
        if "$" not in command.command and command.command not in self.commands:
            command.command = f"${command.command}"
        if command.command in self.commands:
            await self.commands[command.command][0](message, command.args)

    async def get_user_from_message(self, message: Message):
        return (await self.api.users.get(message.from_id))[0]


if not os.path.isfile("config.json"):
    with open("config.json", 'w') as file:
        json.dump({"access_token": ""}, file)
    print("Enter your token in config.json")
    exit(0)

bot = VkBot()
ai = AI()


@bot.on.message()
async def message(message: Message):
    text = message.text.lower()
    user = await bot.get_user_from_message(message)
    ai_recognize = ai.recognite(message.text)

    # print(ai_recognize.type)

    if ai_recognize.type == "CENSURE":
        bot.add_warning_msg(message)
        await message.answer(f"Это ваше {bot.get_warnings_msg(message)} предупреждение")
        pass

    if ai_recognize.type == "COMMAND":  # Если получили комманду
        await bot.call_command(message, command=ai_recognize.command)

    # print(ai_recognize.call_me, ai_recognize.type)

    if not ai_recognize.call_me:
        return

    if ai_recognize.type == "LIBRARY_HELP":  # Если получили запрос о библиотеке
        librarys = bot.database.get_all_library_names()
        library_name = ""

        for library in librarys:  # Перебираем все имена всех библиотек и пытаемся понять, какое из имен подходит
            if library[0] in text:
                library_name = library[0]
                break
            for _lib_name in library[1]:
                if _lib_name in text:
                    library_name = library[0]
                    break
        else:
            await message.answer("Библиотека не найдена!")
            return

        library = bot.database.get_library(library_name)
        books = ""
        if len(library[1]):
            for book in library[1]:
                books += f"{book[1]} - {book[0].capitalize()}: {book[2].capitalize()}\n"

        hrefs = ""
        if len(library[2]):
            for href in library[2]:
                hrefs += f"{href[0].capitalize()}: {href[1]}\n"

        await message.answer(f"Библиотека: {library_name}\n\n"
                             f"[Описание]:\n{(library[0] if len(library[0]) else 'Нету')}\n\n"
                             f"[Советую почитать]:\n{(books if len(books) else 'Ничего')}\n\n"
                             f"[Полезные ссылки]:\n{hrefs if len(hrefs) else 'Отсутствуют'}")


@bot.command()
async def help(message: Message, args: list):   # Комманда help
    if not len(args):
        msg = ""

        for lib in bot.commands:
            if lib.startswith("$") or lib == "help":
                continue
            com = bot.commands[lib]
            msg += f"/{lib} [coms] - {com[1]}\n\n"

        await message.answer(msg + "Для подробной помощи напишите - /help [command]")
        return
    if args[0].replace("/", "") in bot.commands:
        com = bot.commands[args[0].replace("/", "")]

        msg = "Доступные сокращения:"
        for alias in com[3]:
            msg += f" /{alias},"
        msg = msg[:-1] + "\n\n"

        await message.answer(msg + com[2])
        return
    else:
        await message.answer("Ничем не могу вам помочь!")
        return


@bot.command(["библ"],
             description="Работа со списком библиотек",
             big_desc="/library new  [lib_name] - добавить библиотеку\n\n"
                      "/library set-desc [lib_name]  [desc] - установить описание\n\n"
                      "/library add-href [lib_name]  [href_name]  [href_desc] - добавить ссылку\n\n"
                      "/library add-book [lib_name]  [book_name]  [book_author]  [book_description] - добавить "
                      "книгу\n\n")
async def library(message: Message, args):
    print(args)
    if len(args) < 2:
        await message.answer("Слишком мало аргуметов!")
        return
    if "new" in args[0]:
        if bot.database.new_library(args[1]):
            await message.answer(f"Библиотека {args[1]} успешно добавлена")
        else:
            await message.answer(f"Библиотека {args[1]} уже существует")
        return

    if len(args) < 3:
        await message.answer("Слишком мало аргуметов!")
        return
    if "set-desc" in args[0]:
        if bot.database.set_library_description(args[1], args[2]):
            await message.answer(f"Описание изменено!")
        else:
            await message.answer(f"Библиотека {args[1]} не найдена!")
        return
    if "del-href" in args[0]:
        if bot.database.del_library_href(args[1], args[2]):
            await message.answer(f"Ссылка удалена!")
        else:
            await message.answer(f"Библиотека {args[1]} или ссылка {args[2]} не найдена!")
        return
    if "del-book" in args[0]:
        if bot.database.del_library_book(args[1], args[2]):
            await message.answer(f"Книга удалена!")
        else:
            await message.answer(f"Библиотека {args[1]} или книга {args[2]} не найдена!")
        return

    if len(args) < 4:
        await message.answer("Слишком мало аргуметов!")
        return
    if "add-href" in args[0]:
        if bot.database.add_library_href(args[1], args[2], args[3]):
            await message.answer(f"Ссылка успешно добавлна")
        else:
            await message.answer(f"Библиотека {args[1]} не найдена или ссылка {args[1]} уже есть!")
        return

    if len(args) < 5:
        await message.answer("Слишком мало аргуметов!")
        return
    if "add-book" in args[0]:
        if bot.database.add_library_book(args[1], args[2], args[3], args[4]):
            await message.answer(f"Книга успешно добавлна")
        else:
            await message.answer(f"Библиотека {args[1]} не найдена или книга {args[1]} уже есть!")
        return


print("!Run!")

bot.run_forever()
