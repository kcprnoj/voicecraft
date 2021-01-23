import sys
import sounddevice as sd
import numpy as np
from time import sleep
from PyQt5 import QtCore, QtWidgets, uic
from styles import LOW_STYLE, MEDIUM_STYLE, HIGH_STYLE
from threading import get_ident


qtcreator_file = "MainWindow.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, recognizer):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.recognizer = recognizer
        self.volume_thread = VolumeUpdateThread(self)
        self.deleted = False
        self.stop = False
        self.init_ui()

    def init_ui(self):
        self.progress.setStyleSheet(LOW_STYLE)
        self.playButton.clicked.connect(self.play_button)
        self.stopButton.clicked.connect(self.stop_button)
        self.sendButton.clicked.connect(self.send_button)

        self.show()
        self.volume_thread.start()

    def closeEvent(self, event):
        self.recognizer.worker.give_command("stop")
        self.recognizer.running = False
        self.deleted = True

    def change_volume(self, value):
        if self.stop:
            return

        self.progress.setValue(value)

        if value > 70:
            self.progress.setStyleSheet(LOW_STYLE)
        elif value > 30:
            self.progress.setStyleSheet(MEDIUM_STYLE)
        else:
            self.progress.setStyleSheet(HIGH_STYLE)

    def stop_button(self):
        self.stop = True
        self.recognizer.stop = True
        self.recognizer.worker.give_command("stop")
        self.progress.setValue(0)

    def play_button(self):
        self.stop = False
        self.recognizer.stop = False

    def send_button(self):
        if self.lineSend.text() != "":
            print(f"({get_ident()}) Giving command : " + self.lineSend.text())
            self.recognizer.worker.give_command(self.lineSend.text())
            self.lineSend.setText("")


class VolumeUpdateThread(QtCore.QThread):

    sig = QtCore.pyqtSignal(int)

    def __init__(self, window: MainWindow):
        super().__init__()
        self.window = window
        self.sig.connect(window.change_volume)
        self.volume = 0

    def run(self):
        def print_sound(indata, outdata, frames, time_in, status):
            self.volume = np.linalg.norm(indata) * 10

        with sd.Stream(callback=print_sound):
            while not self.window.deleted:
                sleep(1/100)
                if self.window.progress.value != self.volume:
                    self.sig.emit(self.volume)


def show_window(recognizer):
    app = QtWidgets.QApplication(sys.argv)
    MainWindow(recognizer)
    sys.exit(app.exec_())
