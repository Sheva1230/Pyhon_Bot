import json
import random
import re
import os

import vkbottle

from AI import AI, AIMessageTypes
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

    has_censure = ai.has_censure(text)   # Проверяем наличие цензуры
    if has_censure > -1:   # -1 означает, что цензура не обнаружена
        if has_censure == 0:   # Если полученна цензура не высокого уровня
            await message.answer("Пожалуйста, постарайтесь воздержаться от таких выражений")
        elif has_censure == 1:   # Если цензура высокого уровня
            await message.answer("Вы сказали очень плохое слово!")
            bot.add_warning_msg(message)
            await message.answer(f"Это ваше {bot.get_warnings_msg(message)} предупреждение!")

    recognited = ai.recognite(text)   # Получаем тип сообщения

    if recognited == AIMessageTypes.HELLO:   # Если это приветствие
        name = (await bot.api.users.get(message.from_id))[0].first_name
        tema = ai.get_tema(text)    # Запрашиваем тематику сообщения
        if tema in ai.generated_hello_phrases:   # Если такая тематика присутствует в заготовл. приветствиях
            phrase = ai.generated_hello_phrases[tema][random.randint(0, len(ai.generated_hello_phrases[tema])-1)]
        else:    # Отрабатываем стандартные приветствия
            phrase = ai.generated_hello_phrases["NO_TEMA"][random.randint(0, len(ai.generated_hello_phrases["NO_TEMA"]) - 1)]
        await message.answer(phrase.format(name))

    # Проверка на то, было ли это обращение к боту
    if not len(re.findall("\[club*|python bot\]", text)) and not text.startswith("куниц"):
        return

    if recognited == AIMessageTypes.UNKNOWN:   # Если не удалось определить тип сообщения
        tema = ai.get_tema(text)   # Запрашиваем тематику сообщения

        if tema == "STALKER":
            await message.answer("Не знаю фраер, шо ты вякнул, но я не в обиде")
        elif tema == "BOT":
            await message.answer("#@%#1337$ERROR: Не могу ответить на ваш запрос#52%(^&$@^(%228")
        else:
            await message.answer("Я не понимаю о чем вы говорите!")


print("!Run!")

bot.run_forever()