import re
import json
import random


class Command:
    def __init__(self, command, args):
        self.command: str = command
        self.args: list = args


class AIRecognized:
    def __init__(self):
        self.type = None
        self.call_me = False
        self.command = None


class AI:
    """  Класс, отвечающий за 'понимание речи' """

    def __init__(self):
        """ Загрузка всех конфигов """

        with open("ai_types.json", encoding="utf-8") as file:
            self.ai_types = json.load(file)

        with open("ai_config.json", encoding="utf-8") as file:
            self.ai_config = json.load(file)
        with open("ai_censure.json", encoding="utf-8") as file:
            self.ai_censure = json.load(file)["CENSURE"]

    @staticmethod
    def recognite_for_words(message, words) -> bool:
        """ Проверка на соответствие сообщения и набора слов

            Пример соответствия: message=привет, words=["прив", "здарова"]

            Также существует возможность создавать более сложные наборы слов:
                words=["прив", ["добрый", ["день", "вечер"]]]

            Вложенные списки первого порядка означают, что все слова в них должны быть в тексте, но не обязательно рядом
            Вложенные списки второго порядка означают, что хотя бы одно слово из них должно быть в тексте:

            word=[["добрый", ["день", "вечер"]]]
            ["добрый", ["день", "вечер"]] - вложенный список первого порядка
            ["день", "вечер"] - вложенный список второго порядка

         """
        # print(words)
        for word in words:
            # print("REC:", word, "MSG:", message)
            if isinstance(word, list):
                count = 0
                for word_1 in word:
                    if isinstance(word, list):
                        if len([j for j in word_1 if len(re.findall(j, message))]):
                            count += 1
                    elif len(re.findall(word_1, message)):
                        count += 1
                if count == len(word):
                    return True
            elif len(re.findall(word, message)):
                return True
        return False

    def get_message_type(self, message):
        """ Получить тип сообщения """

        if message.startswith(self.ai_config["command_prefix"]):
            return "COMMAND"

        for type in self.ai_types:
            # print(type)
            if self.recognite_for_words(message, self.ai_types[type]):
                return type

        return "UNKNOWN"

    def censure_check(self, message):
        """ Проверка на цензуру """

        if self.recognite_for_words(message, self.ai_censure):
            return True
        return False

    @staticmethod
    def get_random_answer_by_topic(_from: dict, topic):
        """ Взять рандомный ответ исходя из темы """

        if topic in _from:
            return random.choice(_from[topic])
        return random.choice(_from["NO_TOPIC"])

    def recognite(self, message) -> AIRecognized:
        ai_message = AIRecognized()   # Объект ответа

        # Проверяем, обратились ли к боту
        if len(re.findall("\[club*|python bot\]", message)) or message.startswith("куниц"):
            ai_message.call_me = True
            message = re.sub("\[club*|python bot\]", "", message).replace("куниц", "")
            print("MESSAGE:", message)

        if self.censure_check(message):
            ai_message.type = "CENSURE"
            return ai_message

        message_type = self.get_message_type(message)
        ai_message.type = message_type

        if message_type == "COMMAND":   # Если сообщение это комманда
            message = message.replace(self.ai_config["command_prefix"], "", 1)
            ai_message.command = Command(message.split()[0], None)
            message = message.replace(f"{ai_message.command.command}", "", 1).replace(" ", "", 1)
            ai_message.command.args = message.split("  ")

        return ai_message
