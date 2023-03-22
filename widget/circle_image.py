from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QBrush, QPixmap
from PyQt5.QtWidgets import QWidget


class CircleImage(QWidget):
    def __init__(self):
        super(CircleImage, self).__init__()
        self.circleImage = None

    def setImage(self, image: str, w, h):
        self.resize(w, h)
        image = QPixmap(image)
        self.circleImage = image.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def paintEvent(self, event):
        super(CircleImage, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = Qt.NoPen
        painter.setPen(pen)
        brush = QBrush(self.circleImage)
        painter.setBrush(brush)
        painter.drawRoundedRect(self.rect(), self.width() / 2, self.height() / 2)
