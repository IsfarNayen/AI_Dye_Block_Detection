import math
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt


class Spinner(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(30)
        self.setFixedSize(70, 70)

    def rotate(self):
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        painter.translate(w / 2, h / 2)

        for i in range(12):
            alpha = int(255 * (i + 1) / 12)
            color = QtGui.QColor(59, 130, 246, alpha)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)

            painter.save()
            painter.rotate(self.angle - i * 30)
            painter.drawRoundedRect(22, -4, 14, 8, 4, 4)
            painter.restore()


class LoadingScreen(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(320, 230)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QtWidgets.QFrame()
        card.setStyleSheet("""
        QFrame{
            background:#161a24;
            border-radius:20px;
            border:1px solid rgba(255,255,255,25);
        }
        QLabel{
            color:white;
            border:none;
        }
        """)

        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(12)

        spinner = Spinner()

        title = QtWidgets.QLabel("Analyzing Image")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:20px;font-weight:700;")

        sub = QtWidgets.QLabel("Please wait while AI processes your result...")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet("font-size:13px;color:#b8c1d1;")

        layout.addStretch()
        layout.addWidget(spinner, alignment=Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addStretch()

        outer.addWidget(card)