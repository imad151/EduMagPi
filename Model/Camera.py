import cv2
import numpy as np

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from picamera2 import Picamera2

import time


class CameraThread(QThread):
    frame_captured = pyqtSignal(np.ndarray)

    def __init__(self, idx: int = 0):
        super().__init__()
        self.cam = Picamera2()
        self.cam.configure(self.cam.create_video_configuration(main={"size": (1080, 1080), "format": "RGB888"}, controls={"ExposureTime": 10000}))
        self.cam.start()
        self.running = False
        self.ImageProcessing = ImageProcessing()

    def run(self):
        while self.running:
            if not self.running:
                break
            frame = self.cam.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = self.ImageProcessing.OutputProcessedCameraFrame(frame)
            if frame is not None:
                self.frame_captured.emit(frame)

    def start(self, **kwargs):
        self.running = True
        super().start()

    def stop(self):
        self.running = False
        self.cam.close()
        self.cam = None
        self.quit()
        self.wait()


class ImageProcessing:
    def __init__(self):
        self.frame = None

    def CropImage(self, frame):
        return frame[540-350:540+350, 540-350:540+350]

    def RotateImage(self, frame):
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    def OutputProcessedCameraFrame(self, frame):
        frame = self.RotateImage(self.CropImage(frame))
        return frame

    def GetPos(self, frame):
        if frame is not None:
            w, h, _ = frame.shape
            Image = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            ret, BinaryImage = cv2.threshold(Image, 87, 255, cv2.THRESH_BINARY_INV)
            kernel = np.ones((5, 5), np.uint8)
            dilate = cv2.dilate(BinaryImage, kernel, iterations=1)
            contours, _ = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                contour = max(contours, key=cv2.contourArea)
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return np.array([cx, cy])

        return None


class CameraHandler:
    def __init__(self, window: QMainWindow):
        self.window = window

        self.CameraThread = CameraThread()
        self.ImageProcessing = ImageProcessing()

        self.InitializeUi()
        self.ConnectSignals()
        self.StartThread()

        self.ShowFrame = False
        self.frame = None
        self.ElementsFrame = None

        self.drawn_points = None
        self.point = False

        self.outline = False
        self.outlined_points = None

        self.drawn_line = None
        self.line = False
        
        self.increment = 1


    def InitializeUi(self):
        self.CamView = self.window.findChild(QGraphicsView, "CamView")
        self.CameraCheckbox = self.window.findChild(QGroupBox, "CameraCheckbox")

        self.CamScene = QGraphicsScene()
        self.CamView.setScene(self.CamScene)

    def ConnectSignals(self):
        self.CameraCheckbox.toggled.connect(self.CamEnabled)
        self.CameraThread.frame_captured.connect(self.DisplayFrame)

    def StartThread(self):
        self.CameraThread.start()

    def CamEnabled(self):
        if self.CameraCheckbox.isChecked():
            self.ShowFrame = True
            self.CameraThread.running = True

        else:
            self.ShowFrame = False
            self.CameraThread.running = False

    def DisplayFrame(self, frame):
        if self.ShowFrame:
            self.CamScene.clear()
            self.frame = frame
            if self.point or self.outline or self.line:
                self.ElementsFrame = np.zeros_like(frame, dtype=np.uint8)
                self.DrawPoints()
                self.DrawLines()
                self.HighlightElements()
                
                frame = cv2.addWeighted(frame, 0.9, self.ElementsFrame, 1.0, 10)

            
            w, h, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.CamScene.addPixmap(QPixmap.fromImage(q_img))
            self.CamView.fitInView(self.CamScene.sceneRect(), Qt.KeepAspectRatio)
        else:
            self.CamScene.clear()

    def DrawPoints(self):
        if self.point:
            if self.drawn_points is not None:
                points = self.drawn_points
                m, n = points.shape
                for i in range(m):
                    color = tuple(int(c) for c in points[i][2:5])
                    cv2.circle(self.ElementsFrame,
                           (int(points[i][0]), int(points[i][1])),
                           thickness=-1, color=color, radius=5)

    def HighlightElements(self):
        if self.outline:
            m, n = self.outlined_points.shape
            for i in range(m):
                color = tuple(int(c) for c in self.outlined_points[i][2:5])
                cv2.circle(self.ElementsFrame,
                           (int(self.outlined_points[i][0]), int(self.outlined_points[i][1])),
                           thickness=1, radius=5, color=color)

    def DrawLines(self):
        if self.line:
            m, n = self.drawn_line.shape
            for i in range(0, m-1, self.increment):
                color = tuple(int(c) for c in self.drawn_line[i][2:5])
                cv2.line(self.ElementsFrame, (int(self.drawn_line[i][0]), int(self.drawn_line[i][1])),
                         (int(self.drawn_line[i+1][0]), int(self.drawn_line[i+1][1])),
                         color=color, thickness=1)
                

    def SendRobotPos(self):
        return self.ImageProcessing.GetPos(self.frame)

    def SaveFrame(self, file_name='img.png', file2_name='images/overlayimg'):
        frame = cv2.addWeighted(self.frame, 0.8, self.ElementsFrame, 1.0, 10)
        cv2.imwrite(file_name, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if self.ElementsFrame is not None:
            cv2.imwrite(file2_name, cv2.cvtColor(self.ElementsFrame, cv2.COLOR_BGR2RGB))

    def closeEvent(self, event):
        self.outline = False
        self.outlined_point = None
        self.line = False
        self.drawn_line = None
        self.ElementsFrame = None
        self.frame = None
        self.CameraThread.stop()
        self.CamScene.clear()
        event.accept()
