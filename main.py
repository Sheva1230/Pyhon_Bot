import json
import os
import random

from AI import AI, Command
from database import Database, DefaultTypes
from vkbottle.bot import Bot, Message, rules


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
            msg = await self.commands[command.command][0](message, command.args)
            if msg is not None:
                await message.answer(msg)

    async def get_user_from_message(self, message: Message):
        return (await self.api.users.get(message.from_id))[0]

    async def get_user_from_id(self, id):
        return (await self.api.users.get(id))[0]


if not os.path.isfile("config.json"):
    with open("config.json", 'w') as file:
        json.dump({"access_token": ""}, file)
    print("Enter your token in config.json")
    exit(0)

bot = VkBot()
ai = AI()


@bot.on.message(rules.ChatActionRule("chat_invite_user"))
async def group_join(message: Message):
    # print(message)
    print("Invite: ", message.action.member_id)
    if message.action.member_id == -206069307:
        bot.database.add_chat(message.chat_id)
        return "Всем привет!"
    else:
        user = await bot.get_user_from_id(message.action.member_id)
        hi_phrases = ["Привет, {}", "Приветствую тебя, {}, добро пожаловать в беседу!"]
        return random.choice(hi_phrases).format(user.first_name)


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
        print(com)

        msg = "Доступные сокращения:"
        for alias in com[3]:
            msg += f" /{alias},"
        msg = msg[:-1] + "\n\n"

        await message.answer(msg + com[2])
        return
    else:
        await message.answer("Ничем не могу вам помочь!")
        return


@bot.command(["sets"],
             description="Настройки беседы",
             big_desc="/settings list - список настроек беседы\n\n"
                      "/settings set [name] [value]")
async def settings(message: Message, args):
    args_count = len(args)
    less_args_count = "Слишком мало аргуметов!"

    if args_count < 1:
        return less_args_count

    print(args)

    if args[0] == "list":
        msg = ""
        av_chat_settings = list(bot.database.available_chat_settings)

        if args_count > 1:
            try:
                args[1] = int(args[1]) - 1

                if args[1]*5 > len(av_chat_settings):
                    av_chat_settings = av_chat_settings[:-5]
                else:
                    av_chat_settings = av_chat_settings[args[2]*5:args[2]*5+5]

                for setting in av_chat_settings:
                    msg += f"{setting} = {bot.database.get_chat_setting(message.chat_id, setting_name=setting)}\n"
                return msg

            except TypeError:
                pass

        for setting in av_chat_settings[:5]:
            msg += f"{setting} = {bot.database.get_chat_setting(message.chat_id, setting_name=setting)}\n"
        return msg

    if args_count < 3:
        return less_args_count

    if args[0] == "set":
        if args[1] not in bot.database.available_chat_settings:
            return f"Не найдено: {args[1]}"

        bot.database.set_chat_setting(message.chat_id, args[1], args[2])
        return f"{args[1]} = {bot.database.get_chat_setting(message.chat_id, setting_name=args[1])}"


@bot.command(["библ"],
             description="Работа со списком библиотек",
             big_desc="/library new [lib_name] - добавить библиотеку\n\n"
                      "/library set-desc [lib_name] [desc] - установить описание\n\n"
                      "/library add-href [lib_name] [href_name] [href_desc] - добавить ссылку\n\n"
                      "/library add-book [lib_name] [book_name] [book_author] [book_description] - добавить "
                      "книгу\n\n")
async def library(message: Message, args):
    print(args)
    if len(args) < 2:
        return "Слишком мало аргуметов!"
    if "new" in args[0]:
        if bot.database.new_library(args[1]):
            return f"Библиотека {args[1]} успешно добавлена"
        else:
            return f"Библиотека {args[1]} уже существует"

    if len(args) < 3:
        return "Слишком мало аргуметов!"
    if "set-desc" in args[0]:
        if bot.database.set_library_description(args[1], args[2]):
            return f"Описание изменено!"
        else:
            return f"Библиотека {args[1]} не найдена!"
    if "del-href" in args[0]:
        if bot.database.del_library_href(args[1], args[2]):
            return f"Ссылка удалена!"
        else:
            return f"Библиотека {args[1]} или ссылка {args[2]} не найдена!"
    if "del-book" in args[0]:
        if bot.database.del_library_book(args[1], args[2]):
            return f"Книга удалена!"
        else:
            return f"Библиотека {args[1]} или книга {args[2]} не найдена!"

    if len(args) < 4:
        return "Слишком мало аргуметов!"

    if "add-href" in args[0]:
        if bot.database.add_library_href(args[1], args[2], args[3]):
            return f"Ссылка успешно добавлна"
        else:
            return f"Библиотека {args[1]} не найдена или ссылка {args[1]} уже есть!"

    if len(args) < 5:
        return "Слишком мало аргуметов!"
    if "add-book" in args[0]:
        if bot.database.add_library_book(args[1], args[2], args[3], args[4]):
            return f"Книга успешно добавлна"
        else:
            return f"Библиотека {args[1]} не найдена или книга {args[1]} уже есть!"


print("!Run!")

bot.run_forever()
