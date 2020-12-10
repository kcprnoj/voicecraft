import speech_recognition as sr
import keyboard as kb
import time
import threading
from word2number import w2n


def press_key(key):
    kb.press(key)
    time.sleep(50 / 1000)


def release_key(key):
    kb.release(key)


class WorkingThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        self.words = []
        self.commands = []
        self.running = True
        self.adding = False
        self.possible_commands = {"run": (press_key, "w", release_key), "left": (press_key, "a", release_key),
                                  "right": (press_key, "d", release_key), "back": (press_key, "s", release_key),
                                  "inventory": (self.hit_key, "e"), "jump": (press_key, " ", release_key),
                                  "space": (press_key, " ", release_key), "walk": (press_key, "w", release_key),
                                  "exit": (exit, 0), "stop": None, "next": None, "f***": (self.hit_key, " "),
                                  "select": [self.hit_key, None]}
        self.input_commands = {"select": [self.hit_key, None]}

    def run(self):
        while self.running:
            self.lock.acquire()
            commands = self.commands
            for command in commands:
                command[0](command[1])
            self.lock.release()

    def give_command(self, sentence):
        words = sentence.split()

        for word in words:
            if word not in self.possible_commands and word not in w2n.american_number_system \
                    and word not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
                print(f"({threading.get_ident()}) Some of the words do not match with possible")
                return

        self.lock.acquire()
        add_input = False
        for word in words:
            if word == "next":
                self.adding = True
                print(f"({threading.get_ident()}) Adding next command")
                continue
            elif word == "stop":
                self.clear_commands()
                print(f"({threading.get_ident()}) Stopping, clearing list")
                break
            elif not self.adding:
                print(f"({threading.get_ident()}) Clearing list")
                self.clear_commands()
            else:
                self.adding = False

            if word.lower() in self.input_commands:
                add_input = True
                self.adding = True
            elif add_input:
                try:
                    self.commands[-1][1] = w2n.word_to_num(word)
                except ValueError:
                    print(f"({threading.get_ident()}) Wrong number, ignoring select ")
                    self.commands.pop()
                add_input = False
                self.adding = False
                continue

            print(f"({threading.get_ident()}) Appending command {self.possible_commands[word.lower()]}")
            self.commands.append(self.possible_commands[word.lower()])
        self.lock.release()

    def clear_commands(self):
        for command in self.commands:
            if len(command) == 3:
                command[2](command[1])
        self.commands.clear()

    def hit_key(self, key):
        if key is not None:
            print(f"({threading.get_ident()}) Hitting key : {key}")
            press_key(str(key))
            release_key(str(key))
            self.remove_command(self.hit_key)

    def remove_command(self, command):
        for c in self.commands:
            if command in c:
                if len(c) == 3:
                    c[2](c[1])
                self.commands.remove(c)


class RecognizingThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.running = True
        self.worker = WorkingThread()

    def run(self):
        r = sr.Recognizer()
        self.worker.start()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=1)
            while self.running:
                word = ""
                print(f"({threading.get_ident()}) Speak : ")
                audio = r.listen(source)
                try:
                    if word == "":
                        word = r.recognize_google(audio)
                        print(word)
                        if word != "":
                            self.worker.give_command(word)
                            if word == "exit":
                                exit(0)
                except sr.UnknownValueError:
                    print(f"({threading.get_ident()}) Could not understand audio")
                    r.adjust_for_ambient_noise(source, duration=1)


if __name__ == "__main__":
    recognizer = RecognizingThread()
    recognizer.start()
