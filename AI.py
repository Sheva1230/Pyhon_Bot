import re
import json
import random


class Command:
    """ Информация о комманде """

    def __init__(self, command, args):
        self.command: str = command
        self.args: list = args


class AIRecognized:
    """ Ответ на вызов функции recognite класса  AI"""

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
            loaded = json.load(file)

            censure = loaded["CENSURE"]
            alphabet = loaded["ALPHABET"]

        if loaded["need_update"]:
            loaded["RE_CENSURE"] = []

            for word in censure:   # Пробразование цензурных слов в регул. выражения с помощью алфавита
                gen_word = word

                for buk in alphabet:
                    if buk in gen_word:
                        gen = buk
                        double_buk = False
                        for _buk in alphabet[buk]:
                            gen += " " + _buk
                            if len(_buk) > 1:
                                double_buk = True
                        if not double_buk:
                            gen = f"[{gen.replace(' ', '')}]"
                        else:
                            gen = f"(?:{gen.replace(' ', '|')})"
                        
                        gen_word = gen_word.replace(buk, gen)

                loaded["RE_CENSURE"].append(gen_word)
                loaded["need_update"] = False  # Нужно ли при след. запуске обновить список рег. выражений

        with open("ai_censure.json", 'w', encoding="utf-8") as file:
            json.dump(loaded, file, indent=2)

        """with open("ai_censure.json", encoding="utf-8") as file:
            s = file.read()
        with open("ai_censure.json", 'w', encoding="utf-8") as file:
            print(s)
            file.write(s)"""

        self.ai_censure = loaded["RE_CENSURE"]

    @staticmethod
    def recognite_for_words(message, words) -> bool:
        """ Проверка на соответствие сообщения и набора слов

            Пример соответствия: message=привет, words=["прив", "здарова"]

            Также существует возможность создавать более сложные наборы слов:
                words=["прив", ["добрый", ["день", "вечер"]]]

            Вложенные списки первого порядка означают, что все слова в них должны быть в тексте, но не обязательно рядом
            Вложенные списки второго порядка означают, что хотя бы одно слово из них должно быть в тексте:

            words=[["добрый", ["день", "вечер"]]]
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

    def recognite(self, orig_message: str) -> AIRecognized:
        ai_message = AIRecognized()   # Объект ответа

        message = orig_message.lower()

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
            orig_message = orig_message.replace(self.ai_config["command_prefix"], "", 1)  # Удаляем префикс
            ai_message.command = Command(orig_message.split()[0], [])  # Создаем объект с описанием комманды
            orig_message = orig_message.replace(f"{ai_message.command.command}", "", 1)  # Удаляем название комманды

            big_args = re.findall('[^/]["].*[^/]["]', orig_message)  # Ишем "большие" аргументы

            for big_arg in range(len(big_args)):  # Заменяем "большие" аргументы на символ: "
                big_args[big_arg] = big_args[big_arg][1:]
                orig_message = orig_message.replace(big_args[big_arg], "\"")
            orig_message = orig_message.split()

            counter = 0
            for arg in orig_message:
                if arg == "" or arg == " ":
                    continue

                if arg == "\"":  # Если встречаесс символ: ", то берем элемент из списка "больших" аргументов
                    ai_message.command.args.append(big_args[counter])
                    counter += 1
                    continue
                ai_message.command.args.append(arg)

        return ai_message
