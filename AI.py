import re


class AIMessageTypes:
    """ Типы сообщений """

    UNKNOWN = -1  #
    START = 0
    HELLO = 1
    WHAT_YOU_CAN = 2


class AI:
    """  Класс, отвечающий за 'понимание речи' """

    # Фразы приветствия, рассортированные по тематикам
    generated_hello_phrases = {
        "NO_TEMA": ["Привет {}!",
                    "Здравствуй {}, я могучий бот!",
                    "Просто здравствуй {}, просто как дела..."],
        "STALKER": ["Приветствую тебя, путник {}!",
                    "Проходи {}, не задерживайся."],
        "BOT": ["Привет бип@ {} @бопб@п. С чего ты вз@л, что я ![кожанный мешок]?",
                "Привет {}. Ты ошибся. Я просто [кожаный мешок]"]
    }

    # Тематики сообщений и их ключевые слова
    temas = {
        "STALKER": [
            "сталкер",
            "меченый",
        ],
        "BOT": [
            "бот",
            "машина",
            "не человек"
        ]
    }

    # Зацензуренные слова
    censure = {
        1: ["хуй", "бля", "сука", "чмо", "пид[о]*р"],
        0: ["писька", "какашка", "писюн"],
    }

    # Другие ключевые слова
    start_words = ["старт", "начать"]
    hello_words = ["привет", "здравствуй", "здарова", "хай", ["добрый", ["день", "вечер"]]]

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

    def recognite(self, message):
        """ Получить тип сообщения """
        if self.recognite_for_words(message, self.start_words):
            return AIMessageTypes.START
        if self.recognite_for_words(message, self.hello_words):
            return AIMessageTypes.HELLO
        return AIMessageTypes.UNKNOWN

    def get_tema(self, message):
        """ Получить тематику сообщения """
        for tema in self.temas:
            if self.recognite_for_words(message, self.temas[tema]):
                return tema
        return "NO_TEMA"

    def has_censure(self, message):
        """ Проверка сообщения на цензуру """
        for censure_level in self.censure:
            if self.recognite_for_words(message, self.censure[censure_level]):
                return censure_level
        return -1
