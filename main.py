import sys
import os
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QIcon

from main_ui import Ui_MainWindow
from drag_and_drop_event import DragDropFrame
from backend import SegmentationBackend

base_dir = os.path.dirname(os.path.abspath(__file__))

backend = SegmentationBackend()
backend.load_models()

class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.icon_set(
            self.ui.uploadIconbutton,
            os.path.join(base_dir, "asset", "upload_icon.png"),
            100, 100
        )
        self.icon_set(
            self.ui.logoPushbutton,
            os.path.join(base_dir, "asset", "app_logo.png"),
            25, 25
        )

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._drag_active = False
        self._drag_position = QPoint()

        self.ui.closeButton.clicked.connect(self.close_win)
        self.ui.minimizeButton.clicked.connect(self.showMinimized)
        self.ui.uploadImagebutton.clicked.connect(self.open_file_dialog)

        self.setup_drag_drop_area()



    def setup_drag_drop_area(self):
        old_frame = self.ui.mainBoxcontainer
        parent = old_frame.parent()
        geometry = old_frame.geometry()

        # Save child widgets from old frame
        children = old_frame.findChildren(QtWidgets.QWidget, options=QtCore.Qt.FindDirectChildrenOnly)

        # Create new drag-drop frame
        new_frame = DragDropFrame(parent)
        new_frame.setGeometry(geometry)
        new_frame.setObjectName("mainBoxcontainer")
        new_frame.setStyleSheet(old_frame.styleSheet())
        new_frame.show()

        # Move old children into new frame
        for child in children:
            child.setParent(new_frame)
            child.show()

        # Reposition children if needed
        # Usually geometry is preserved, but raise important widgets
        if hasattr(self.ui, "uploadImagebutton"):
            self.ui.uploadImagebutton.raise_()
        if hasattr(self.ui, "uploadIconbutton"):
            self.ui.uploadIconbutton.raise_()

        # Hide old frame
        old_frame.hide()
        old_frame.deleteLater()

        # Replace reference
        self.ui.mainBoxcontainer = new_frame
        self.ui.mainBoxcontainer.fileDropped.connect(self.handle_dropped_image)

    def open_file_dialog(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            #  print("Selected image:", file_path)
            temp = backend.predict_image_from_gui(file_path)
            print(temp)

    def handle_dropped_image(self, file_path):
        # print("Dropped image:", file_path)
        temp = backend.predict_image_from_gui(file_path)
        print(temp)

    def icon_set(self, widget, icon_path, w, h):
        if isinstance(widget, QtWidgets.QPushButton):
            widget.setIcon(QIcon(icon_path))
            widget.setIconSize(QtCore.QSize(w, h))
        elif isinstance(widget, QtWidgets.QLabel):
            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                print("Image not found:", icon_path)
                return
            pixmap = pixmap.scaled(
                w, h,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )
            widget.setPixmap(pixmap)

    def close_win(self):
        self.close()

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