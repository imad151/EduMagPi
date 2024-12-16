import time
import os
import sys

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import numpy as np

from Model.ControlBox import ControlsHandler
from Model.Camera import CameraHandler, ImageProcessing
from Model.Instructions import InstructionsPane

def resource_path(file_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, file_path)
    return os.path.abspath(file_path)
    
    
class Game1(QMainWindow):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        uifile = resource_path("UI/Game1.ui")
        uic.loadUi(uifile, self)
        self.setWindowTitle("Whack a Mole")

        self.InitializeClasses()
        self.InitializeUi()
        self.ConnectSignals()
        self.SetupTimer()

        self.duration = 0
        self.start_time = 0
        self.target = np.array([[350, 350]])
        self.color = np.array([[255, 0, 0]])

    def InitializeClasses(self):
        self.Camera = CameraHandler(self)
        self.Controls = ControlsHandler(self)

    def InitializeUi(self):
        self.StartButton = self.findChild(QCheckBox, 'StartButton')
        self.ScoreSpinbox = self.findChild(QSpinBox, 'ScoreSpinbox')
        self.GameTimer = self.findChild(QSpinBox, 'GameTimer')

    def ConnectSignals(self):
        self.StartButton.toggled.connect(self.StartGame)
        self.InstructionsButton.pressed.connect(self.ShowInstructions)

    def SetupTimer(self, fps: int = 10):
        self.timer = QTimer()
        self.timer.timeout.connect(self.GameLogic)


    def StartGame(self, fps=10):
        if self.StartButton.isChecked():
            if not self.Camera.CameraCheckbox.isChecked():
                self.Camera.CameraCheckbox.setChecked(True)
            self.Camera.point = True
            self.duration = self.GameTimer.value()
            self.start_time = time.time()
            self.ScoreSpinbox.setValue(0)
            self.target = np.array([[350, 350]])
            self.timer.start(1000 // fps)


        else:
            self.StopGame()

    def StopGame(self):
        try: self.timer.stop()
        except: pass

        self.Camera.drawn_points = None
        self.GameTimer.setValue(60)

    def GameLogic(self):
        elapsed_time = time.time() - self.start_time
        if self.StartButton.isChecked() and elapsed_time <= self.duration:
            self.GameTimer.setValue(int(self.duration - elapsed_time))
            target_point = np.hstack((self.target, self.color))
            self.Camera.drawn_points = target_point
            pos = self.Camera.SendRobotPos()

            if pos is not None:
                if np.linalg.norm(self.target - pos) <= 15:
                    self.target = self.RNG()
                    self.Camera.drawn_points = np.hstack((self.target, self.color))
                    self.ScoreSpinbox.setValue(self.ScoreSpinbox.value() + 1)

        else:
            self.StartButton.setChecked(False)
            self.Camera.point = False

    def RNG(self, max_distance=80):
        phi = np.random.uniform(0, 2 * np.pi)
        r = np.random.uniform(0, max_distance)

        x = r * np.cos(phi) + 350
        y = r * np.sin(phi) + 350

        return np.array([[x, y]])

    def ShowInstructions(self):
        self.Instructions = InstructionsPane()
        self.Instructions.ShowInstructionsPane(1)
        self.Instructions.show()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.Camera.closeEvent(event)
        self.Controls.closeEvent()
        self.timer.stop()
        self.closed.emit()
