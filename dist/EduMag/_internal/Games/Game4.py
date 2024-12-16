from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from PyQt5 import uic

from Model.Camera import CameraHandler
from Model.ControlBox import ControlsHandler
from Model.Instructions import InstructionsPane
from Model.MST import MST

import numpy as np

from datetime import datetime
import os
import sys

import subprocess
import platform


def resource_path(file_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, file_path)
    return os.path.abspath(file_path)


class Game4(QMainWindow):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        uifile = resource_path('UI/Game4.ui')
        uic.loadUi(uifile, self)
        self.setWindowTitle("Route Designer")

        self.InitializeUi()
        self.InitializeClasses()
        self.ConnectSignals()
        self.SetupTimer()

        self.nodes = np.array([])
        self.ConnectedNodes = np.array([])
        self.ROI = (300, 450)
        self.SelectedNode = None
        self.Camera.increment = 2

    def InitializeUi(self):
        self.StartButton = self.findChild(QCheckBox, "StartButton")
        self.CheckButton = self.findChild(QPushButton, "CheckButton")
        self.DifficultyBox = self.findChild(QComboBox, "DifficultyBox")
        self.CameraCheckbox = self.findChild(QGroupBox, "CameraCheckbox")
        self.ScoreSpinbox = self.findChild(QSpinBox, "ScoreBox")
        self.GiveUpButton = self.findChild(QPushButton, "ShowSolutionButton")
        self.SavePNGButton = self.findChild(QPushButton, "SaveImageButton")
        self.InstructionsButton = self.findChild(QPushButton, "InstructionsButton")

    def InitializeClasses(self):
        self.Camera = CameraHandler(self)
        self.Controls = ControlsHandler(self)

    def ConnectSignals(self):
        self.StartButton.toggled.connect(self.StartGame)
        self.CheckButton.pressed.connect(self.AnalyzeUserInput)
        self.GiveUpButton.pressed.connect(self.UserGiveUp)
        self.SavePNGButton.pressed.connect(self.SaveImage)
        self.InstructionsButton.pressed.connect(self.ShowInstructions)

    def SetupTimer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.JoystickControls)
        

    def StartGame(self):
        if self.StartButton.isChecked():
            self.DifficultyBox.setEnabled(False)
            self.CameraCheckbox.setChecked(True)
            self.GenerateNodes()
            self.DisplayNodes()
            self.ScoreSpinbox.setValue(0)
            self.timer.start(100)
        else:
            self.EndGame()
            self.DifficultyBox.setEnabled(True)

    def EndGame(self):
        self.timer.stop()
        self.Camera.point = False
        self.Camera.line = False
        self.Camera.outline = False
        self.nodes = np.array([])
        self.ConnectedNodes = np.array([])
        self.SelectedNode = None
        if self.GiveUpButton.text() == 'Hide Solution':
            self.GiveUpButton.setText('Show Solution')

    def GenerateNodes(self):
        difficulty = self.DifficultyBox.currentText()
        if difficulty == 'Medium': num_nodes = 7
        elif difficulty == 'Hard': num_nodes = 9
        else: num_nodes = 5  # 5 nodes for all unknown cases + easy

        num_clusters = np.random.randint(2, 5)
        cluster_centre = np.random.uniform(300, 450, (num_clusters, 2))
        max_distance = 100
        min_distance = 50

        nodes = []
        for _ in range(num_nodes):
            while True:
                if np.random.rand() == 0.5:
                    x = np.random.normal(350, max_distance)
                    y = np.random.normal(350, max_distance)
                else:
                    curr_cluster_idx = np.random.choice(num_clusters)
                    curr_cluster = cluster_centre[curr_cluster_idx]

                    x = np.random.normal(curr_cluster[0], max_distance)
                    y = np.random.normal(curr_cluster[1], max_distance)

                x = np.clip(x, 300, 450)
                y = np.clip(y, 300, 450)

                if len(nodes) == 0 or np.all(np.linalg.norm(np.array(nodes) - np.array([x, y]), axis=1) >= min_distance):
                    nodes.append([x, y])
                    break

        self.nodes = np.array(nodes)
        

    def DisplayNodes(self):
        if not self.CameraCheckbox.isChecked():
            self.CameraCheckbox.setChecked(True)

        self.Camera.point = True
        color = np.array([255, 0, 0])
        temp = np.tile(color, (self.nodes.shape[0], 1))
        nodes_with_color = np.hstack((self.nodes, temp))
        self.Camera.drawn_points = nodes_with_color

    def JoystickControls(self):
        joy_input = self.Controls.GetJoyButtons()
        if joy_input == 'a':
            self.CheckForNode()

        if joy_input == 'start':
            self.ResetConnections()

        if joy_input == 'b':
            self.UndoAction()

    def CheckForNode(self):
        pos = self.Camera.SendRobotPos()
        if pos is not None:
            close_node = None
            for node in self.nodes:
                if np.linalg.norm(pos - node) <= 20:
                    close_node = np.array(node)
            if close_node is not None:
                if self.SelectedNode is None:
                    self.SelectedNode = close_node
                    self.HighlightSelectedNode()
                else:
                    if np.any(self.SelectedNode != close_node):
                        self.ConnectNodes(close_node)
                        self.SelectedNode = None
                        self.RemoveHighlight()

    def ResetConnections(self):
        self.ConnectedNodes = np.array([])
        self.Camera.line = False
        self.Camera.outline = False
        self.SelectedNode = None
        if self.GiveUpButton.text() == 'Hide Solution':
            self.GiveUpButton.setText('Show Solution')

    def HighlightSelectedNode(self, color=(0, 0, 255)):
        color = np.array([color])
        node_with_color = np.hstack((np.expand_dims(self.SelectedNode, axis=0), color))
        self.Camera.outline = True
        self.Camera.outlined_points = node_with_color

    def RemoveHighlight(self):
        if self.SelectedNode is None:
            self.Camera.outline = False
            self.Camera.outlined_points = None

    def ConnectNodes(self, node, color=(0, 255, 0)):
        color = np.array([color])
        if self.ConnectedNodes.shape[0] > 1:
            new_row = np.hstack((np.array([[node[0], node[1]]]), color))
            prev_row = np.hstack((np.expand_dims(self.SelectedNode, axis=0), color))
            self.ConnectedNodes = np.vstack((self.ConnectedNodes, prev_row, new_row))

        else:
            temp = np.hstack((np.array([[self.SelectedNode[0], self.SelectedNode[1]]]), color))

            self.ConnectedNodes = np.vstack((temp, np.hstack((np.array([[node[0], node[1]]]), color))))

        self.DrawConnectedNodes()

    def DrawConnectedNodes(self):
        self.Camera.line = True
        self.Camera.drawn_line = self.ConnectedNodes

    def AnalyzeUserInput(self):
        if hasattr(self, 'ConnectedNodes'):
            if self.ConnectedNodes.size > 1:
                user_input_points = self.ConnectedNodes[:, :2]
                user_input_points = np.array(self.RemoveDuplicates(user_input_points))
                arranged_points = np.array(self.CalculateMST())

                formatted_points = []
                for start_x, start_y, end_x, end_y in arranged_points:
                    formatted_points.append([start_x, start_y])
                    formatted_points.append([end_x, end_y])

                formatted_points = np.array(formatted_points)

                Lu = np.sqrt(np.sum(np.diff(user_input_points, axis=0) ** 2, axis=1))
                Lu = np.sum(Lu)

                Li = np.sqrt(np.sum(np.diff(formatted_points, axis=0) ** 2, axis=1))
                Li = np.sum(Li)

                Eu = user_input_points.shape[0] - 1
                Ei = formatted_points.shape[0] - 1

                difficulty = self.DifficultyBox.currentText()
                k = 0.001
                if difficulty == 'Medium':
                    k = 0.005
                elif difficulty == 'Hard':
                    k = 0.009

                print(f"Lu: {Lu}, Li: {Li}, Eu: {Eu}, Ei: {Ei}")
                Score = max(0, (1 - (abs((Lu - Li)) / Li) - k * abs(Eu - Ei)))
                print(f'{Score:.2f}')
                self.ScoreSpinbox.setValue(int(Score*100))

    def RemoveDuplicates(self, points):
        unique_points = [points[0]]
        for i in range(1, len(points)):
            if not np.array_equal(points[i], points[i - 1]):
                unique_points.append(points[i])

        cleaned_points = []
        seen = set()
        for i in range(len(unique_points) - 1):
            pair = (tuple(unique_points[i]), tuple(unique_points[i+1]))
            if pair not in seen:
                cleaned_points.append(unique_points[i])
                seen.add(pair)

        cleaned_points.append(points[-1])

        return cleaned_points

    def UserGiveUp(self):
        if self.StartButton.isChecked():
            if self.GiveUpButton.text() == 'Show Solution':
                self.GiveUpButton.setText("Hide Solution")
                self.ShowSolution()
            else:
                self.GiveUpButton.setText('Show Solution')
                if len(self.ConnectedNodes) > 0:
                    self.Camera.drawn_line = self.ConnectedNodes
                else:
                    self.Camera.line = False
                    self.Camera.drawn_line = None

    def ShowSolution(self, color=(0, 255, 0)):
        color = np.array([color])
        arranged_points = self.CalculateMST()

        formatted_points = []
        for start_x, start_y, end_x, end_y in arranged_points:
            formatted_points.append([start_x, start_y])
            formatted_points.append([end_x, end_y])

        formatted_points = np.array(formatted_points)
        color = np.tile(color, (formatted_points.shape[0], 1))
        formatted_points = np.hstack((formatted_points, color))
        self.Camera.line = True
        self.Camera.drawn_line = formatted_points

    def CalculateMST(self) -> list:
        MST_instance = MST(self.nodes)

        return MST_instance.CalculateMST()

    def UndoAction(self):
        if self.SelectedNode is not None:
            self.SelectedNode = None
            self.Camera.outline = False

        elif self.ConnectedNodes.shape[0] >= 1:
            self.ConnectedNodes = self.ConnectedNodes[:-2]
            self.Camera.drawn_line = self.ConnectedNodes

    def SaveImage(self, file_name='path_img', file2_name='full_img', folder='images'):
        if self.CameraCheckbox.isChecked():
            os.makedirs(folder, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = os.path.join(folder, f'{file_name}-{timestamp}.png')
            file2_name = os.path.join(folder, f'{file2_name}-{timestamp}.png')

            self.Camera.SaveFrame(file_name=file_name, file2_name=file2_name)
            print(f'Image saved as {file_name}')

            path = os.path.abspath(folder)
            if platform.system() == 'Windows':
                subprocess.Popen(['explorer', path])
            elif platform.system() == "Linux":
                subprocess.Popen(['xdg-open', path])

    def ShowInstructions(self, game_index=4):
        self.Instructions = InstructionsPane()
        self.Instructions.ShowInstructionsPane(idx=game_index)
        self.Instructions.show()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.Camera.closeEvent(event)
        self.Controls.closeEvent()
        self.closed.emit()
