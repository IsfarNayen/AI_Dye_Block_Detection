import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QPoint

from main_ui import Ui_MainWindow


class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Create UI first
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # === Frameless Window ===
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # === Drag by mouse ===
        self._drag_active = False
        self._drag_position = QPoint()

        # Connect buttons after setupUi
        # Use the correct object name from Designer
        self.ui.closeButton.clicked.connect(self.close_win)

        # If you also want minimize button:
        self.ui.minimizeButton.clicked.connect(self.showMinimized)

    def close_win(self):
        self.close()

    # Mouse events for dragging frameless window
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())