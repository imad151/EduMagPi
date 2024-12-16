import sys
import time
import os

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import pyqtSignal

from Model.Camera import CameraHandler
from Model.ControlBox import ControlsHandler

from Model.Instructions import InstructionsPane

def resource_path(file_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, file_path)
    return os.path.abspath(file_path)


class MainWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self):
        super(MainWindow, self).__init__()
        ui_file = resource_path("UI/MainPage.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("Main Page")
        self.InitializeClasses()

        self.InstructionsButton.pressed.connect(self.ShowInstructions)

    def InitializeClasses(self):
        self.Camera = CameraHandler(self)
        self.Controls = ControlsHandler(self)
        self.Controls.Edumag.DisplayField = True
        

    def ShowInstructions(self):
        self.InstructionsPane = InstructionsPane()
        self.InstructionsPane.ShowInstructionsPane(0)
        self.InstructionsPane.show()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.Camera.closeEvent(event)
        self.Controls.closeEvent()
        self.closed.emit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myapp = MainWindow()
    myapp.showMaximized()
    sys.exit(app.exec_())

