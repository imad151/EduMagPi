from PyQt5 import uic
from PyQt5.QtWidgets import *

import os
import sys


def resource_path(file_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, file_path)
    return os.path.abspath(file_path)


class InstructionsPane(QMainWindow):
    def __init__(self):
        super().__init__()

    def ShowInstructionsPane(self, idx: int) -> None:
        if idx == 0:  # For MainPage
            uifile = resource_path('UI/InstructionsMain.ui')
            uic.loadUi(uifile, self)

        elif idx == 1:  # Game 1
            uifile = resource_path('UI/Game1Instructions.ui')
            uic.loadUi(uifile, self)

        elif idx == 2:  # Game 2
            uifile = resource_path('UI/Game2Instructions.ui')
            uic.loadUi(uifile, self)

        elif idx == 3:  # Game 3
            uifile = resource_path('UI/Game3Instructions.ui')
            uic.loadUi(uifile, self)
        elif idx == 4:  # Game 4
            uifile = resource_path('UI/Game4Instructions.ui')
            uic.loadUi(uifile, self)
        else:
            print(f'Invalid index of Instructions: {idx}')

