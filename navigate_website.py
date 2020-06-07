import os
import io
import json
import pyaudio
from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QUrl
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
import re
import requests
import sys
import threading
from vosk import Model, KaldiRecognizer
from snips_nlu import SnipsNLUEngine
from snips_nlu.default_configs import CONFIG_FR

class Nlu:
    nlu_engine = SnipsNLUEngine(config=CONFIG_FR)

    def __init__(self,fileNlu):
        with io.open(fileNlu) as f:
            sample_dataset = json.load(f)
        self.nlu_engine = self.nlu_engine.fit(sample_dataset)

    def parse(self,text):
        return self.nlu_engine.parse(text)

class VocalThread(QThread):
    get_vocal_message = pyqtSignal(str)

    def run(self):
    ##PYAUDIO
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
        stream.start_stream()
        nlu = Nlu("nlu/fr_FR/navigate_website.json")

        ##VOSK
        model = Model("model/fr_FR")
        rec = KaldiRecognizer(model, 16000)
        while True:
            data = stream.read(8000, exception_on_overflow = False)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = re.findall(r'(?<=text")(?:\s*\:\s*)(".{0,23}?(?=")")', rec.Result(), re.IGNORECASE+re.DOTALL)
                if len(result) > 0:
                    parsing = nlu.parse(result[0].replace('"','').replace("'"," "))
                    if parsing["intent"]["intentName"] is not None:
                        self.get_vocal_message.emit(json.dumps(parsing))


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("navigate web site")
        self.actual_url = "https://juliengabryelewicz.fr"
        self.disply_width = 640
        self.display_height = 480
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(self.actual_url))
        vbox = QVBoxLayout()
        vbox.addWidget(self.browser)
        self.setLayout(vbox)

        self.thread = VocalThread()
        self.thread.get_vocal_message.connect(self.go_to_page)
        self.thread.start()

    @pyqtSlot(str)
    def go_to_page(self, text):
        json_nlu = json.loads(text)
        switcher = {
        "blog": "https://juliengabryelewicz.fr/blog",
        "cv": "https://juliengabryelewicz.fr/page/cv",
        "page d'accueil": "https://juliengabryelewicz.fr/",
        "mentions légales": "https://juliengabryelewicz.fr/page/mentions-legales",
        }
        if(len(json_nlu["slots"]) > 0):
            new_link = switcher.get(json_nlu["slots"][0]["value"]["value"], "")
            if new_link != "":
                self.actual_url = new_link
                self.browser.setUrl(QUrl(self.actual_url))


        
    
if __name__=="__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())