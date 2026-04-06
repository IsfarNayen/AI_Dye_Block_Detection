import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QIcon
base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
from main_ui import Ui_MainWindow
from drag_and_drop_event import DragDropFrame


class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Create UI first
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        
        self.icon_set(self.ui.uploadIconbutton, os.path.join(base_dir, "asset", "upload_icon.png"), 100, 100)
        self.icon_set(self.ui.logoPushbutton, os.path.join(base_dir, "asset", "app_logo.png"), 25, 25)
        
        

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

        
        
        # === Drag & Drop event when image file is hovered ===
        old_frame = self.ui.mainBoxcontainer
        parent = old_frame.parent()
        geometry = old_frame.geometry()

        self.ui.mainBoxcontainer = DragDropFrame(parent)
        self.ui.mainBoxcontainer.setGeometry(geometry)
        self.ui.mainBoxcontainer.setObjectName("mainBoxcontainer")
        self.ui.mainBoxcontainer.show()
        self.ui.mainBoxcontainer.fileDropped.connect(self.handle_dropped_image)
    
    
    
    
    # === Image path is saved when dropped an image ===
    def handle_dropped_image(self, file_path):
        print("Dropped image:", file_path)
     
    
    
    #Function for setting different icons
    def icon_set(self, widget, icon_path, w, h):
        """Set icons safely depending on widget type."""
        if isinstance(widget, QtWidgets.QPushButton):
            widget.setIcon(QIcon(icon_path))
            widget.setIconSize(QtCore.QSize(w, h))
        elif isinstance(widget, QtWidgets.QLabel):
            pixmap = QPixmap(icon_path).scaled(
                w, h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            widget.setPixmap(pixmap)


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
