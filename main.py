import speech_recognition as sr
import keyboard as kb
import time
import threading
import mouse
from word2number import w2n
from window import show_window


def press_key(key):
    kb.press(key)
    time.sleep(50 / 1000)


def release_key(key):
    kb.release(key)


def run_direction(word):
    if word == "right":
        return "d"
    elif word == "left":
        return "a"
    elif word == "back":
        return "s"
    else:
        return "w"


def mouse_direction(word):
    if word == "right":
        return [30, 0]
    elif word == "left":
        return [-30, 0]
    elif word == "back":
        return [0, 30]
    else:
        return [0, -30]


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
                                  "select": [self.hit_key, None], "up": [self.mouse_move, [0, -30]],
                                  "down": [self.mouse_move, [0, 30]], "mouse": [self.mouse_move, [0, 30]]}
        self.input_commands = {"select": [self.hit_key, None], "run": [press_key, "", release_key],
                               "mouse": [self.mouse_move, [0, 30]]}

        self.direction = ("right", "left", "back")

    def run(self):
        while self.running:
            self.lock.acquire()
            commands = self.commands
            for command in commands:
                command[0](command[1])
            self.lock.release()

    def give_command(self, sentence: str):
        words = sentence.split()

        for word in words:
            if word.lower() not in self.possible_commands and word not in w2n.american_number_system \
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
                if self.commands[-1][0] == self.hit_key:
                    try:
                        self.commands[-1][1] = w2n.word_to_num(word)
                    except ValueError:
                        print(f"({threading.get_ident()}) Wrong number, ignoring select ")
                        self.commands.pop()
                elif self.commands[-1][0] == press_key:
                    self.commands[-1][1] = run_direction(word)
                elif self.commands[-1][0] == self.mouse_move:
                    self.commands[-1][1] = mouse_direction(word)
                add_input = False
                self.adding = False
                continue

            print(f"({threading.get_ident()}) Appending command {self.possible_commands[word.lower()]}")
            self.commands.append(self.possible_commands[word.lower()])

        if add_input and self.adding:
            if self.commands[-1][0] == self.hit_key:
                self.commands[-1][1] = 0
            elif self.commands[-1][0] == press_key:
                self.commands[-1][1] = "w"
            elif self.commands[-1][0] == self.mouse_move:
                self.commands[-1][1] = [0, -30]
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
