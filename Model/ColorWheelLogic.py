import math

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class PaintWheel(QWidget):
    colorChanged = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.CurrentColor = QColor(255, 0, 0)
        self.dragging = False  # Flag to track dragging state
        self.setMinimumSize(1, 1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self.DrawRing(painter)
        self.ColorRing(painter)

    def DrawRing(self, painter):
        size = self.size()
        radius = self.width() // 2
        self.center = QPoint(radius, radius)
        self.outer_rect = QRect(0, 0, size.width(), size.height())
        self.inner_radius = radius * 0.5  # Inner ring
        self.marker_radius = radius * 0.7

        self.inner_rect = QRect(
            int(self.center.x() - self.inner_radius),
            int(self.center.y() - self.inner_radius),
            int(self.inner_radius * 2),
            int(self.inner_radius * 2)
        )

    def ColorRing(self, painter):
        for angle in range(360):
            color = QColor.fromHsv(angle, 255, 255)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawPie(self.outer_rect, angle * 16, 16)

        # Draw the inner circle (background in the center)
        painter.setBrush(self.palette().window())
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.center, int(self.inner_radius), int(self.inner_radius))

        # Draw the color marker indicating the current color
        hue = self.CurrentColor.hue()
        
        marker_x = int(self.center.x() + self.marker_radius * math.cos(math.radians(hue)))
        marker_y = int(self.center.y() - self.marker_radius * math.sin(math.radians(hue)))

        painter.setBrush(self.CurrentColor)
        painter.setPen(Qt.black)
        painter.drawEllipse(QPoint(marker_x, marker_y), 5, 5)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            center = self.rect().center()
            dx, dy = event.x() - center.x(), center.y() - event.y()

            # Check if the click is within the ring
            if math.hypot(dx, dy) <= self.size().width() // 2 - 10:
                hue = self.CalculateAngle(dx, dy)
                self.SetColor(QColor.fromHsv(hue, 255, 255))
                self.dragging = True  # Start dragging

    def mouseMoveEvent(self, event):
        if self.dragging:
            center = self.rect().center()
            dx, dy = event.x() - center.x(), center.y() - event.y()

            # Calculate the angle and set the color while dragging
            hue = self.CalculateAngle(dx, dy)
            self.SetColor(QColor.fromHsv(hue, 255, 255))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False  # Stop dragging

    def wheelEvent(self, event):
        delta = event.angleDelta().y() // 120  # 1 notch of wheel
        current_hue = self.CurrentColor.hue()
        new_hue = (current_hue + delta) % 360
        self.SetColor(QColor.fromHsv(new_hue, 255, 255))

    def UpdateFromJoystickAngle(self, angle: int):
        """
        Changes marker position with joystick
        :param angle:
        :return:
        """
        self.SetColor(QColor.fromHsv(angle % 360, 255, 255))

    def resizeEvent(self, event):
        size = min(event.size().width(), event.size().height())
        self.resize(size, size)

    def CalculateAngle(self, dx, dy):
        return int((math.degrees(math.atan2(dy, dx)) + 360) % 360)

    def SetColor(self, color):
        self.CurrentColor = color
        self.colorChanged.emit(color)
        self.update()  # Trigger repaint to update the color wheel
