import numpy as np

import os
import sys

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from Model.Camera import CameraHandler
from Model.EduMag import EduMagHandler
from Model.Instructions import InstructionsPane
from Model.Keyboard import ArrowKeyAngle


def resource_path(file_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, file_path)
    return os.path.abspath(file_path)
    

class Game2(QMainWindow):
    closed = pyqtSignal()

    def __init__(self):
        super(QMainWindow, self).__init__()
        uifile = resource_path('UI/Table.ui')
        uic.loadUi(uifile, self)
        self.setWindowTitle("Maze Navigator")
        self.InitializeClasses()
        self.InitializeUi()
        self.ConnectSignals()

    def InitializeClasses(self):
        self.Edumag = EduMagHandler(self)
        self.Edumag.DisplayField = True
        self.Camera = CameraHandler(self)
        self.Keyboard = ArrowKeyAngle()

    def InitializeUi(self):
        self.AddButton = self.findChild(QPushButton, "AddButton")
        self.RemoveOneButton = self.findChild(QPushButton, "RemoveOneButton")
        self.RemoveAllButton = self.findChild(QPushButton, "RemoveAllButton")
        self.ExecuteButton = self.findChild(QPushButton, "ExecuteButton")
        self.PauseCheckBox = self.findChild(QCheckBox, "PauseButton")

        self.B_spinbox = self.findChild(QDoubleSpinBox, "B_spinbox")
        self.G_spinbox = self.findChild(QDoubleSpinBox, "G_spinbox")
        self.theta_spinbox = self.findChild(QDoubleSpinBox, "theta_spinbox")
        self.time_spinbox = self.findChild(QDoubleSpinBox, "time_spinbox")

        self.MaxG = self.findChild(QDoubleSpinBox, 'MaxG')

        self.CommandsBox = self.findChild(QTableWidget, "CommandsBox")
        self.InstructionsButton = self.findChild(QPushButton, "InstructionsButton")

    def ConnectSignals(self):
        self.B_spinbox.valueChanged.connect(self.SetMaxG)
        self.AddButton.pressed.connect(self.AddParam)
        self.RemoveOneButton.pressed.connect(self.RemoveParam)  # Remove Current Params
        self.RemoveAllButton.pressed.connect(self.RemoveParams)  # Remove All Params (notice the s at the end)

        self.ExecuteButton.pressed.connect(self.ExecuteCommands)
        self.InstructionsButton.pressed.connect(self.ShowInstructions)

        self.CommandsBox.selectionModel().selectionChanged.connect(self.ShowSelectedVecField)

    def AddParam(self):
        B = self.B_spinbox.value()
        G = self.G_spinbox.value()
        theta = self.theta_spinbox.value()
        time = self.time_spinbox.value()

        if time != 0:
            if B != 0:
                inputs = [B, G, theta, time]
                I = self.Edumag.GetCurrents(B, G, int(theta))

                if not np.all(I == 0):
                    row_count = self.CommandsBox.rowCount()
                    self.CommandsBox.setRowCount(row_count + 1)

                    for column, item in enumerate(inputs):
                        self.CommandsBox.setItem(row_count, column, QTableWidgetItem(str(item)))

                    self.ResizeTableWidget()

    def RemoveParam(self):
        selected_item = self.CommandsBox.selectedItems()
        if selected_item:
            for item in selected_item:
                try:
                    row = self.CommandsBox.row(item)
                    self.CommandsBox.removeRow(row)
                except:
                    pass

        else:
            pass

    def RemoveParams(self):
        self.CommandsBox.clearContents()
        self.CommandsBox.setRowCount(0)

    def ExecuteCommands(self):
        rows = self.CommandsBox.rowCount()
        cols = self.CommandsBox.columnCount()
        data = np.zeros((rows, cols), dtype=float)

        for row in range(rows):
            for col in range(cols):
                item = self.CommandsBox.item(row, col)
                if item is not None and item.text() != "":
                    data[row, col] = float(item.text())

        self.iter = iter(data)
        self.ProcessNext()

    def ProcessNext(self):
        if not self.PauseCheckBox.isChecked():
            try:
                row = next(self.iter)
                param = row[:3]
                delay = int(row[-1])

                self.Edumag.UpdateCurrents(param[0], param[1], param[2])

                QTimer.singleShot(delay * 1000, self.ProcessNext)

            except StopIteration:
                self.Edumag.ResetCurrents()
                pass
            
        else:
            self.Edumag.ResetCurrents()

    def ShowSelectedVecField(self):
        SelectedItem = self.CommandsBox.selectedItems()
        if SelectedItem:
            SelectedRow = SelectedItem[0].row()

            RowParams = []

            for cols in range(4):
                item = self.CommandsBox.item(SelectedRow, cols)
                RowParams.append(float(item.text()) if item else "None")

            I = self.Edumag.GetCurrents(RowParams[0], RowParams[1], int(RowParams[2]))
            self.Edumag.UpdateField(I)

    def SetMaxG(self):
        B = self.B_spinbox.value()
        g_max = self.GetMaxG(B)
        self.G_spinbox.setSingleStep(g_max * 0.1)
        self.G_spinbox.setMaximum(g_max - g_max * 0.1)
        self.MaxG.setValue(g_max - g_max * 0.1)

    def GetMaxG(self, B):
        return -38.5633 * B + 997.3362

    def ShowInstructions(self):
        self.InstructionsPane = InstructionsPane()
        self.InstructionsPane.ShowInstructionsPane(2)
        self.InstructionsPane.show()

    def ResizeTableWidget(self):
        w = self.CommandsBox.viewport().width()
        cols = self.CommandsBox.columnCount()

        col_width = w // cols

        for col in range(cols):
            self.CommandsBox.setColumnWidth(col, col_width)

    def KeyBoardControls(self):
        if self.KeyboardCheckbox.isChecked():
            theta = self.Keyboard.get_angle()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.Camera.closeEvent(event)
        self.closed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ResizeTableWidget()
        self.Edumag.ResizeVecField()
