import folium
from folium.plugins import MarkerCluster
import os
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

class VocalThread(QThread):
    get_vocal_message = pyqtSignal(str)

    def run(self):
    ##PYAUDIO
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
        stream.start_stream()

        ##VOSK
        model = Model("model/fr_FR")
        rec = KaldiRecognizer(model, 16000)
        while True:
            data = stream.read(8000, exception_on_overflow = False)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = re.findall(r'(?<=text")(?:\s*\:\s*)(".{0,23}?(?=")")', rec.Result(), re.IGNORECASE+re.DOTALL)[0].replace('"','')
                if len(result) > 0:
                    self.get_vocal_message.emit(result)


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("change map")
        self.disply_width = 640
        self.display_height = 480
        self.browser = QWebEngineView()
        self.show_location(0,0)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(current_dir, 'show_city.html')
        url = QUrl.fromLocalFile(filename)
        self.browser.setUrl(url)
        vbox = QVBoxLayout()
        vbox.addWidget(self.browser)
        self.setLayout(vbox)

        self.thread = VocalThread()
        self.thread.get_vocal_message.connect(self.search_location)
        self.thread.start()

    @pyqtSlot(str)
    def search_location(self, text):
        result = requests.get("http://www.mapquestapi.com/geocoding/v1/address?key=your-key&location="+text)
        print(text)
        result_text = result.text
        lat = float(re.findall(r'(?<="lat")(?:\s*\:\s*)(.{0,23}?(?=,))', result_text, re.IGNORECASE+re.DOTALL)[0])
        lng = float(re.findall(r'(?<="lng")(?:\s*\:\s*)(.{0,23}?(?=}))', result_text, re.IGNORECASE+re.DOTALL)[0])
        statuscode = int(re.findall(r'(?<="statuscode")(?:\s*\:\s*)(.{0,23}?(?=,))', result_text, re.IGNORECASE+re.DOTALL)[0])
        if statuscode == 0:
            self.show_location(lat, lng)
            self.reload_map()

    def reload_map(self):
        self.browser.reload()

    def show_location(self, lat, lng):
        mappy = folium.Map(location=[lat,lng],tiles = "OpenStreetMap",zoom_start = 13)
        folium.Marker([lat,lng]).add_to(mappy)
        mappy.save('show_city.html')
    
if __name__=="__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())