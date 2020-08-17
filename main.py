import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QFileDialog, QMainWindow, QVBoxLayout, QSizePolicy, QAction, QMenu
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

import pyaudio
import wave
import struct
import numpy as np
from scipy import signal

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self._main = QWidget()
        self.setCentralWidget(self._main)
        self.title = 'Waveform Viewer'
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.cmaps = ['jet', 'viridis', 'plasma', 'inferno', 'magma', 'Greys']
        self.cmap = self.cmaps[0]
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.layout = QVBoxLayout(self._main)

        self.fig = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.fig)
        self.layout.addWidget(self.canvas)
        self.addToolBar(NavigationToolbar(self.canvas, self))
        self.ax = self.fig.subplots()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Amplitude')

        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        editMenu = mainMenu.addMenu('Edit')
        viewMenu = mainMenu.addMenu('View')
        toolsMenu = mainMenu.addMenu('Tools')
        helpMenu = mainMenu.addMenu('Help')

        openButton = QAction('Open File...', self)
        openButton.setShortcut('Ctrl+O')
        openButton.triggered.connect(self.openFileNameDialog)
        fileMenu.addAction(openButton)

        exitButton = QAction(QIcon('exit24.png'), 'Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.setStatusTip('Exit application')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

        self.time_domain = QAction('Time Domain', self, checkable=True)
        self.time_domain.setChecked(True)
        self.time_domain.triggered.connect(self.handleTimeDomain)
        viewMenu.addAction(self.time_domain)

        self.spectrogram = QAction('Spectrogram', self, checkable=True)
        self.spectrogram.setChecked(False)
        self.spectrogram.triggered.connect(self.handleSpectrogram)
        viewMenu.addAction(self.spectrogram)

        self.selColourMap = QMenu('Select Colour Map', self)
        toolsMenu.addMenu(self.selColourMap)
        for cmap in self.cmaps:
            action = QAction(cmap, self, checkable=True)
            self.selColourMap.addAction(action)
            if cmap == self.cmap:
                action.setChecked(True)
            action.triggered.connect(self.update_cmap)
        self.show()

    def update_cmap(self, checked):
        action = self.sender()
        self.cmap = action.text()
        for item in self.selColourMap.actions():
            if item != action:
                item.setChecked(False)
        self.update_plot()

    def read_wav_file(self, filename):
        self.waveform = wave.open(filename, 'rb')
        self.p = pyaudio.PyAudio()
        # Open a .Stream object to write the WAV file to
        # 'output = True' indicates that the sound will be played rather than recorded
        stream = self.p.open(format = self.p.get_format_from_width(self.waveform.getsampwidth()),
                                channels = self.waveform.getnchannels(),
                                rate = self.waveform.getframerate(),
                                output = True)
        self.data_length = self.waveform.getnframes()
        self.wav_data = []
        for i in range(0, self.data_length):
            self.data = self.waveform.readframes(1)
            self.data = struct.unpack("<h", self.data)
            self.wav_data.append(self.data[0])
        self.wav_data = np.array(self.wav_data)
        self.fs = self.waveform.getframerate()

        self.update_plot()

    def handleTimeDomain(self):
        self.time_domain.setChecked(True)
        self.spectrogram.setChecked(False)
        self.update_plot()

    def handleSpectrogram(self):
        self.spectrogram.setChecked(True)
        self.time_domain.setChecked(False)
        self.update_plot()

    def update_plot(self):
        self.ax.clear()
        if self.time_domain.isChecked():
            time_base = np.linspace(0, len(self.wav_data) / self.fs, num=len(self.wav_data))
            self.ax.plot(time_base, self.wav_data, color='k')
            self.ax.set_xlabel('Time (s)')
            self.ax.set_ylabel('Amplitude')
            self.ax.set_xlim((min(time_base),max(time_base)))
            self.ax.grid(True)
        else:
            self.freq_base, self.time_base, self.spec_data = signal.spectrogram(self.wav_data, self.fs)
            self.ax.pcolormesh(self.time_base, self.freq_base, np.log(self.spec_data), cmap=self.cmap)
            self.ax.set_ylabel('Frequency (Hz)')
            self.ax.set_xlabel('Time (s)')
        self.canvas.draw()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,'Open File', "","All Files (*);;Wave Files (*.wav)", options=options)
        if fileName:
            self.read_wav_file(fileName)

    def saveFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            print(fileName)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
