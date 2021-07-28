import json
import random
import re
import os

import vkbottle

from AI import AI
from database import Database, DefaultTypes
from vkbottle.bot import Bot, Message


class VkBot(Bot):   # Класс бота
    def __init__(self):
        with open("config.json") as file:
            self.config = json.load(file)
            self.database = Database()

            super().__init__(token=self.config["access_token"])

    def add_warning_msg(self, message: Message):   # Добавление пред. пользователю через объект Message
        self.add_warning(message.chat_id, message.from_id)

    def add_warning(self, chat_id, user_id):   # Добавление пред. пользователю через id чата и пользователя
        warnings = self.database.get_field(chat_id, user_id, "warnings", DefaultTypes.INT)

        if warnings is None:
            return

        self.database.set_field(chat_id, user_id, "warnings", warnings+1)

    def get_warnings_msg(self, message: Message):   # Получить пред. пользователя через объект Message
        return self.get_warnings(message.chat_id, message.from_id)

    def get_warnings(self, chat_id, user_id):   # Получить пред. пользователю через id чата и пользователя
        return self.database.get_field(chat_id, user_id, "warnings", DefaultTypes.INT)

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
    ai_recognize = ai.recognite(text)

    # print(ai_recognize.type)

    if ai_recognize.type == "CENSURE":
        bot.add_warning_msg(message)
        await message.answer(f"Это ваше {bot.get_warnings_msg(message)} предупреждение")
        pass

    if ai_recognize.type == "COMMAND":  # Если получили комманду
        args = ai_recognize.command.args
        # print(args)
        if ai_recognize.command.command == "help":
            if not len(args[0]):
                await message.answer("/library [coms] - работа с библиотекой\n\n"
                                     "Для подробной помощи напишите - /help [command]")
                return
            if "library" in args[0]:
                await message.answer("/library new  [lib_name] - добавить библиотеку\n\n"
                                     "/library set-desc [lib_name] [desc] - установить описание\n\n"
                                     "/library add-href [lib_name] [href_name] [href_desc] - добавить ссылку\n\n")
                return
            else:
                await message.answer("Ничем не могу вам помочь!")
                return

        if len(args) < 2:
            await message.answer("Слишком мало аргуметов!")
            return

        if ai_recognize.command.command == "library":
            if args[0] == "new":
                bot.database.new_library(args[1])
                await message.answer(f"Библиотека {args[1]} успешно добавлена")
                return

            if len(args) < 3:
                await message.answer("Слишком мало аргуметов!")
                return
            if args[0] == "set-desc":
                if bot.database.set_library_description(args[1], args[2]):
                    await message.answer(f"Описание изменено!")
                else:
                    await message.answer(f"Библиотека {args[1]} не найдена!")
                return
            if args[0] == "del-href":
                if bot.database.del_library_href(args[1], args[2]):
                    await message.answer(f"Ссылка удалена!")
                else:
                    await message.answer(f"Библиотека {args[1]} или ссылка {args[2]} не найдена!")
                return

            if len(args) < 4:
                await message.answer("Слишком мало аргуметов!")
                return
            if args[0] == "add-href":
                if bot.database.add_library_href(args[1], args[2], args[3]):
                    await message.answer(f"Ссылки успешно добавлны")
                else:
                    await message.answer(f"Библиотека {args[1]} не найдена!")
                return

    # print(ai_recognize.call_me, ai_recognize.type)

    if not ai_recognize.call_me:
        return

    if ai_recognize.type == "LIBRARY_HELP":   # Если получили запрос о библиотеке
        librarys = bot.database.get_all_library_names()
        library_name = ""

        for library in librarys:   # Перебираем все имена всех библиотек и пытаемся понять, какое из имен подходит
            if library[0] in text:
                library_name = library[0]
                break
            for _lib_name in library[1]:
                if _lib_name in text:
                    library_name = library[0]
                    break
        else:
            await message.answer("Библиотека не найдена!")

        # print(library_name)
        library = bot.database.get_library(library_name)

        hrefs = ""
        if len(library[2]):
            for href in library[2]:
                hrefs += f"{href[0]}: {href[1]}\n"

        await message.answer(f"Библиотека: {library_name}\n\n"
                             f"[Описание]:\n{(library[0] if len(library[0]) else 'Нету')}\n\n"
                             f"[Советую почитать]:\n{(library[1] if len(library[1]) else 'Ничего')}\n\n"
                             f"[Полезные ссылки]:\n{hrefs if len(hrefs) else 'Отсутствуют'}")


print("!Run!")

bot.run_forever()