import re
import json
import random


class AIMessageTypes:
    """ Типы сообщений """

    UNKNOWN = -1
    HELLO = 0
    COMMAND = 1


class Command:
    def __init__(self, command, args):
        self.command: str = command
        self.args: list = args


class AICensure:
    def __init__(self, answer, topic):
        self.answer: str = answer
        self.topic = topic


class AIMessage:
    def __init__(self, type, topic, answer):
        self.type = type
        self.topic = topic
        self.answer: str = answer


class AIRecognized:
    def __init__(self):
        self.to_me = False
        self.message: AIMessage = None
        self.command: Command = None
        self.topic = None
        self.censure: AICensure = None
        self.type = None


class AI:
    """  Класс, отвечающий за 'понимание речи' """

    def __init__(self):
        """ Загрузка всех конфигов """

        with open("answer_phrases.json", encoding="utf-8") as file:
            self.answer_phrases = json.load(file)

        with open("key_words.json", encoding="utf-8") as file:
            self.key_words = json.load(file)

        with open("ai_config.json", encoding="utf-8") as file:
            self.ai_config = json.load(file)

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
        for word in words:
            # print(word, message)
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

    def get_topic(self, message):
        """ Получить (возможную) тематику разговора """

        for topic in self.key_words["TOPICS"]:
            if self.recognite_for_words(message, self.key_words["TOPICS"][topic]):
                return topic

        return "NO_TOPIC"

    def get_message_type(self, message):
        """ Получить тип сообщения """

        if message.startswith(self.ai_config["command_prefix"]):
            return AIMessageTypes.COMMAND

        if message.count(" ") > 2:
            _message = message
            message = message.split()
            message = message[0] + " " + message[1]
        print(message)

        if self.recognite_for_words(message, self.key_words["HELLO"]):
            print("WHAT")
            return AIMessageTypes.HELLO

        return AIMessageTypes.UNKNOWN

    def censure_check(self, message):
        """ Проверка на цензуру """

        if self.recognite_for_words(message, self.key_words["CENSURE"]):
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
            ai_message.to_me = True
            message = re.sub("\[club*|python bot\]", message, "").replace("куниц", "")

        message_type = self.get_message_type(message)
        ai_message.type = message_type

        if message_type == AIMessageTypes.COMMAND:   # Если сообщение это комманда
            message = message.replace(self.ai_config["command_prefix"], "")

            ai_message.command = Command(message.split()[0], None)
            if message.count(" "):
                ai_message.command.args = message.split()[1:]
        else:
            topic = self.get_topic(message)
            ai_message.message = AIMessage(message_type, topic, "")

            if message_type == AIMessageTypes.HELLO:
                ai_message.message.answer = self.get_random_answer_by_topic(self.answer_phrases["HELLO"], topic)
            else:
                ai_message.message.answer = self.get_random_answer_by_topic(self.answer_phrases["UNKNOWN"], topic)

        if self.censure_check(message):
            topic = self.get_topic(message)
            ai_message.censure = AICensure(self.get_random_answer_by_topic(self.answer_phrases["CENSURE"], topic), topic)

        return ai_message
