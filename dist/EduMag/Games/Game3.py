import os
import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from PyQt5 import uic

from Model.Camera import CameraHandler
from Model.ControlBox import ControlsHandler
from Model.ColorWheelLogic import PaintWheel
from Model.Instructions import InstructionsPane

import numpy as np
from datetime import datetime

import subprocess
import platform

def resource_path(file_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, file_path)
    return os.path.abspath(file_path)


class Game3(QMainWindow):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        uifile = resource_path('UI/Game3.ui')
        uic.loadUi(uifile, self)
        
        self.setWindowTitle("Paint Game")

        self.InitializeClasses()
        self.InitUi()
        self.ConnectSignals()
        self.SetupTimer()

        self.color = np.array([[255, 0, 0]])  # default red
        self.AllPoints = np.array([])

    def InitializeClasses(self):
        self.Controls = ControlsHandler(self)
        self.Camera = CameraHandler(self)

    def InitUi(self):
        self.ColorWheelWidget = self.findChild(PaintWheel, "ColorWheel")
        self.JoystickCheckbox = self.findChild(QCheckBox, "JoystickCheckbox")
        self.SaveImageButton = self.findChild(QPushButton, "SaveImage")
        self.InstructionsButton = self.findChild(QPushButton, "InstructionsButton")

    def ConnectSignals(self):
        self.ColorWheelWidget.colorChanged.connect(self.ChangeSelectedColor)
        self.SaveImageButton.pressed.connect(self.SaveFrame)
        self.InstructionsButton.pressed.connect(self.ShowInstructions)

    def SetupTimer(self):
        self.timer = QTimer()
        self.timer.start(1000 // 33)
        self.timer.timeout.connect(self.UpdateWheelFromJoystick)
        self.timer.timeout.connect(self.GetJoystickButtons)

    def UpdateWheelFromJoystick(self):
        if self.JoystickCheckbox.isChecked():
            angle = self.Controls.GetRightStickValue()
            if angle is not None:
                self.ColorWheelWidget.UpdateFromJoystickAngle(angle)

    def GetJoystickButtons(self):
        Joy_Input = self.Controls.GetJoyButtons()
        if Joy_Input == 'a':
            self.HandleDraw()
            #time.sleep(0.1)
        if Joy_Input == 'start':
            self.ClearAllElements()

    def HandleDraw(self):
        pos = self.Camera.SendRobotPos()
        if pos is not None:
            current_point_mat = np.hstack((pos.reshape(1, -1), self.color))
            if self.AllPoints.shape[0] >= 1:
                self.AllPoints = np.vstack((self.AllPoints, current_point_mat))
                self.Camera.line = True
                self.Camera.drawn_line = self.AllPoints
            else:
                self.AllPoints = current_point_mat
                self.Camera.point = True
                self.Camera.drawn_points = self.AllPoints

    def ClearAllElements(self):
        self.AllPoints = np.array([])
        
        self.Camera.drawn_points = None
        self.Camera.point = False

        self.Camera.outline = False
        self.Camera.outlined_points = None

        self.Camera.drawn_line = None
        self.Camera.line = False
        
        self.Camera.ElementsFrame = None

    def ChangeSelectedColor(self, color):
        self.color = np.array([[color.red(), color.green(), color.blue()]])

    def SaveFrame(self, file_name='img', file2_name='overlay_img', folder='images'):
        if self.Camera.CameraCheckbox.isChecked():
            os.makedirs(folder, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = os.path.join(folder, f'{file_name}-{timestamp}.png')
            file2_name = os.path.join(folder, f'{file2_name}-{timestamp}.png')

            self.Camera.SaveFrame(file_name=file_name, file2_name=file2_name)
            print(f'Image saved as {file_name}')

            path = os.path.abspath(folder)
            if platform.system() == 'Windows':
                subprocess.Popen(['explorer', path])
            else:
                subprocess.Popen(['xdg-open', path])

    def ShowInstructions(self, game_index=3):
        self.Instructions = InstructionsPane()
        self.Instructions.ShowInstructionsPane(game_index)
        self.Instructions.show()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.Camera.closeEvent(event)
        self.Controls.closeEvent()
        self.closed.emit()
