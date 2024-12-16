import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')
import time

import os
import sys

def resource_path(file_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, file_path)
    return os.path.abspath(file_path)

class EduMag:
    def __init__(self):
        self.B_vec = np.array([[-0.00340, -0.00030, 0.00340, 0.00030], [-0.00030, 0.00340, 0.00030, -0.00340]])
        self.Grad_X = np.array([[-0.23960, 0.16450, -0.23960, 0.16450], [-0.00620, 0.00680, -0.00620, 0.00680]])
        self.Grad_Y = np.array([[-0.00680, 0.00620, -0.00680, 0.00620], [0.16450, -0.23960, 0.16450, -0.23960]])

    def SetFieldForce(self, B: float, F: float, theta: int) -> np.array:
        B /= 1000
        F /= 1000
        theta = np.deg2rad(theta)

        if B == 0:
            return np.array([0, 0, 0, 0])

        unit = np.array([np.cos(theta), np.sin(theta)])

        Breq = np.round(unit * B, 3)
        Freq = np.round(unit * F, 3)

        Sol = np.vstack((self.B_vec, unit.dot(self.Grad_X), unit.dot(self.Grad_Y)))
        I = np.round(np.linalg.pinv(Sol).dot(np.hstack((Breq, Freq))), 3)

        if np.any(I) >= 4:
            return np.array([0, 0, 0, 0])

        else:
            return I


class PlotVectorField:
    def __init__(self):
        self.InitData()
        self.InitPlot()

    def InitData(self):
        filepath = resource_path("Model/VecField_Data.xlsx")
        self.df = pd.read_excel(filepath)

        self.X = self.df['X'].values
        self.Y = self.df['Y'].values

        self.BiX = self.df[['B1X', 'B2X', 'B3X', 'B4X']].values * 1000
        self.BiY = self.df[['B1Y', 'B2Y', 'B3Y', 'B4Y']].values * 1000

    def InitPlot(self):
        self.fig, self.ax = plt.subplots()
        self.fig.set_dpi(70)
        self.quiver = self.ax.quiver(self.X, self.Y, self.X * 0, self.X * 0, self.X * 0, cmap='jet', animated=True)
        self.colorbar = self.fig.colorbar(self.quiver, ax=self.ax, label='Bnet')

        self.ax.set_xlabel('X (mm)')
        self.ax.set_ylabel('Y (mm)')
        self.ax.set_rasterized(True)
        self.ax.grid(False)
        
        self.fig.canvas.draw_idle()
        self.background = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        self.quiver.set_antialiased(False)


    def DrawField(self, I):
        I = I[:, np.newaxis]
        #I = I.T
        BXnet = np.dot(self.BiX, I).ravel()
        BYnet = np.dot(self.BiY, I).ravel()

        Bnet = np.sqrt(BXnet ** 2 + BYnet ** 2)

        try:
            self.quiver.set_UVC(BXnet, BYnet, Bnet)
            #self.quiver.set_array(Bnet)
            self.quiver.set_clim(vmin=np.min(Bnet), vmax=np.max(Bnet))
            #self.quiver.scale = np.max(Bnet) * 10
            self.colorbar.update_normal(self.quiver)
            


        except Exception as e:
            print(f'Error drawing Field: {e}')
            pass


from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Model.SerialCom import ArduinoController as Serial

class EduMagHandler:
    def __init__(self, window):
        super().__init__()

        self.window = window
        self.Edumag = EduMag()
        self.Serial = Serial()

        self.OpenSerialPort()

        self.PlotVectorField = PlotVectorField()
        
        self.DisplayField = False
        self.InitializeUi()

        self.last_current = np.array([0, 0, 0, 0])
        self._background = None
        
    def OpenSerialPort(self):
        try:
            with open("SerialSettings.txt", "r") as file:
                saved_serial = file.read().strip()
                print(saved_serial)
                self.Serial.set_port(saved_serial)
                status = self.Serial.connect()
                if status:
                    print("Serial Connected Successfully")
                else:
                    print("Error connecting to serial")

        except FileNotFoundError:
            print("File Not Found")

    def InitializeUi(self):
        self.VecView = self.window.findChild(QGraphicsView, 'VecView')
        if self.VecView is not None:
            self.VecScene = QGraphicsScene()
            self.VecView.setScene(self.VecScene)
        self.CurrentsLabel = self.window.findChild(QLabel, "CurrentsLabel")
        self.VecViewCheckbox = self.window.findChild(QCheckBox, "VecFieldCheckBox")

    def UpdateCurrents(self, B: float, G: float, theta: int) -> None:
        I = self.Edumag.SetFieldForce(B, G, theta)
        if np.any(abs(I) > 4):
            return
        if np.all(self.last_current != I):
            self.UpdateLabels(I)
            self.SendCurrents(I)
            self.last_current = I

            if self.DisplayField:
               if self.VecViewCheckbox is not None:
                    if self.VecViewCheckbox.isChecked():
                        self.UpdateField(I)
                

    def UpdateField(self, I):
        self.PlotVectorField.DrawField(I)
        self.PlotField(self.PlotVectorField.fig)


    def GetCurrents(self, B: float, G: float, theta: int) -> np.ndarray:
        return self.Edumag.SetFieldForce(B, G, theta)

    def ResetCurrents(self):
        _ = self.Serial.reset()

    def PlotField(self, fig):
        if self.VecView is not None:
            canvas = fig.canvas
            ax = fig.axes[0]
            
            if self._background is None:
                canvas.draw()
                self._background = canvas.copy_from_bbox(fig.bbox)
            
            canvas.restore_region(self._background)

                            
            ax.draw_artist(self.PlotVectorField.quiver)
            canvas.blit(ax.bbox)
                
            #canvas.blit(canvas.figure.bbox)
            w, h = canvas.get_width_height()
            buffer = canvas.buffer_rgba()
            q_img = QImage(buffer, w, h, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(q_img)
            if self.VecScene.items():
                self.VecScene.items()[0].setPixmap(pixmap)

            else:
                self.VecScene.addItem(QGraphicsPixmapItem(pixmap))
            self.ResizeVecField()
        else:
            pass

    def UpdateLabels(self, I):
        if self.CurrentsLabel is not None:
            self.CurrentsLabel.setText(f'I1 = {I[0]:.2f}A, I2 = {I[1]:.2f}A, I3 = {I[2]:.2f}A, I4 = {I[3]:.2f}A ')

    def SendCurrents(self, I):
        self.Serial.set_target_currents(I)

    def ResizeVecField(self):
        self.VecView.fitInView(self.VecScene.sceneRect(), Qt.KeepAspectRatio)

    def resizeEvent(self):
        self.ResizeVecField()
        
    def closeEvent(self):
        status = self.Serial.disconnect()
        if status:
            print("Serial Disconnected")
        else:
            print("serial didn't disconnect properly")
