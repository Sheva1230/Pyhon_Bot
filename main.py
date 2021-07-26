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

    if ai_recognize.censure is not None:
        bot.add_warning_msg(message)
        await message.answer(ai_recognize.censure.answer.format(user.first_name, user.last_name))
        await message.answer(f"Это ваше {bot.get_warnings_msg(message)} предупреждение")
        pass

    if ai_recognize.type == AIMessageTypes.COMMAND:
        if ai_recognize.command.command == "test":
            await message.answer("test passed")

    if ai_recognize.type == AIMessageTypes.HELLO:
        await message.answer(ai_recognize.message.answer.format(user.first_name, user.last_name))

    if not ai_recognize.to_me:
        return

    if ai_recognize.type == AIMessageTypes.UNKNOWN:
        await message.answer(ai_recognize.message.answer)


print("!Run!")

bot.run_forever()