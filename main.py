import speech_recognition as sr
import keyboard as kb
import time
import threading
import mouse
from word2number import w2n
from window import show_window
from image_finder import find_on_screen


def press_key(key: str) -> None:
    kb.press(key)
    time.sleep(50 / 1000)


def release_key(key: str) -> None:
    kb.release(key)


def run_direction(word: str) -> None:
    if word == "right":
        return "d"
    elif word == "left":
        return "a"
    elif word == "back":
        return "s"
    else:
        return "w"


def mouse_direction(word: str) -> None:
    if word == "right":
        return [30, 0]
    elif word == "left":
        return [-30, 0]
    elif word == "back":
        return [0, 30]
    else:
        return [0, -30]


def push(word: str) -> None:
    if word.lower() == 'right':
        if not mouse.is_pressed(button="RIGHT"):
            mouse.press(button="RIGHT")
    else:
        if not mouse.is_pressed():
            mouse.press()


def release_mouse(word: str) -> None:
    if word.lower() == 'right':
        mouse.release(button="RIGHT")
    else:
        mouse.release()


class WorkingThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        self.words = []
        self.commands = []
        self.running = True
        self.adding = False
        self.possible_commands = {"run": [press_key, "w", release_key],
                                  "inventory": (self.hit_key, "e"), "jump": (press_key, " ", release_key),
                                  "space": (press_key, " ", release_key), "walk": [press_key, "w", release_key],
                                  "exit": (exit, 0), "stop": None, "next": None, "f***": (self.hit_key, (exit, 0)),
                                  "select": [self.select, None], "up": [self.mouse_move, [0, -30]],
                                  "down": [self.mouse_move, [0, 30]], "mouse": [self.mouse_move, [0, 30]],
                                  "find": [self.find, "Options"], "click": [self.click, ""],
                                  "hold": [push, "", release_mouse], "escape": (self.hit_key, chr(27)),
                                  "say": [self.say, ""], "creek": [self.click, ""]}
        self.input_commands = {"select": [self.select, None], "run": [press_key, "", release_key],
                               "mouse": [self.mouse_move, [0, 30]], "find": [self.find, "Options"],
                               "click": [self.click, ""], "walk": [press_key, "w", release_key],
                               "hold": [push, "", release_mouse], "say": [self.say, ""],  "creek": [self.click, ""]}

        self.direction = ("right", "left", "back")

    def run(self):
        while self.running:
            self.lock.acquire()
            commands = self.commands
            for command in commands:
                command[0](command[1])
            self.lock.release()

    def give_command(self, sentence: str) -> None :
        words = sentence.split()

        for word in words:
            if word.lower() in self.input_commands:
                break
            elif word.lower() not in self.possible_commands and word not in w2n.american_number_system \
                    and word not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9') and word not in self.direction:
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
                if self.commands[-1][0] == self.select:
                    try:
                        self.commands[-1][1] = w2n.word_to_num(word)
                    except ValueError:
                        print(f"({threading.get_ident()}) Wrong number, ignoring select ")
                        self.commands.pop()
                elif self.commands[-1][0] == press_key:
                    self.commands[-1][1] = run_direction(word)
                elif self.commands[-1][0] == self.mouse_move:
                    self.commands[-1][1] = mouse_direction(word)
                elif self.commands[-1][0] == self.find:
                    sent = ''
                    for w in words[1:len(words)]:
                        sent += w
                    self.commands[-1][1] = sent
                elif self.commands[-1][0] == self.click:
                    self.commands[-1][1] = word
                elif self.commands[-1][0] == self.say:
                    sent = ' '
                    for w in words[1:len(words)]:
                        sent += w + ' '
                    self.commands[-1][1] = sent
                add_input = False
                self.adding = False
                break

            try:
                print(f"({threading.get_ident()}) Appending command {self.possible_commands[word.lower()]}")
                self.commands.append(self.possible_commands[word.lower()])
            except KeyError:
                print(f"({threading.get_ident()}) Wrong command : {word}")

        if add_input and self.adding:
            if self.commands[-1][0] == self.hit_key:
                self.commands[-1][1] = 0
            elif self.commands[-1][0] == press_key:
                self.commands[-1][1] = "w"
            elif self.commands[-1][0] == self.mouse_move:
                self.commands[-1][1] = [0, -30]
            elif self.commands[-1][0] == self.mouse_move:
                self.commands[-1][1] = "Settings"
            self.adding = False

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

    def mouse_move(self, values):
        mouse.move(values[0], values[1], absolute=False, duration=0.5)
        self.remove_command(self.mouse_move)

    def find(self, word):
        pos = find_on_screen(word)
        mouse.move(pos[0], pos[1])
        self.remove_command(self.find)

    def click(self, word):
        if word.lower() == 'right':
            mouse.click(button="RIGHT")
        else:
            mouse.click()
        self.remove_command(self.click)

    def select(self, key):
        if key in (1, 2, 3, 4, 5, 6, 7, 8, 9):
            self.hit_key(key)
        self.remove_command(self.select)

    def say(self, sentence):
        press_key('t')
        release_key('t')

        for char in sentence:
            press_key(char)
            release_key(char)

        press_key('\n')
        release_key('\n')

        self.remove_command(self.say)


class RecognizingThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.running = True
        self.stop = False
        self.worker = WorkingThread()

    def run(self):
        r = sr.Recognizer()
        self.worker.start()
        with sr.Microphone(device_index=1) as source:
            r.adjust_for_ambient_noise(source)
            while self.running:
                word = ""
                print(f"({threading.get_ident()}) Speak : ")
                audio = r.listen(source)
                if not self.running:
                    break
                elif self.stop:
                    print(f"({threading.get_ident()}) Stopped")
                    continue
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
                    r.adjust_for_ambient_noise(source)

            self.worker.running = False


if __name__ == "__main__":
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))

    recognizer = RecognizingThread()
    recognizer.start()
    show_window(recognizer)
