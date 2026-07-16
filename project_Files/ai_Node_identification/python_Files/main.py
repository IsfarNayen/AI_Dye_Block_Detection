import sys
import os
import shutil

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QIcon

from ..UI.skeleton_UI_files.node_Analysis_drag_drop import Ui_MainWindow
from .drag_and_drop_event import DragDropFrame
from .node_Analysis_details_main import MainApp as nodeDetailswindow
from .worker_class_for_heavy_processing import PredictionWorker
from .loading_screen import LoadingScreen

base_dir = os.path.dirname(os.path.abspath(__file__))


class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setFixedSize(self.size())

        self.result_window = None
        self.worker = None
        self.loading_dialog = None

        self.icon_set(self.ui.logoPushbutton, os.path.join(base_dir, "..", "..", "..", "drag_and_drop_node_icon.png"), 10, 10)

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

        children = old_frame.findChildren(
            QtWidgets.QWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )

        new_frame = DragDropFrame(parent)
        new_frame.setGeometry(geometry)
        new_frame.setObjectName("mainBoxcontainer")
        new_frame.setStyleSheet(old_frame.styleSheet())
        new_frame.fileDropped.connect(self.handle_dropped_image)
        new_frame.show()

        for child in children:
            child.setParent(new_frame)
            child.show()

        if hasattr(self.ui, "uploadImagebutton"):
            self.ui.uploadImagebutton.raise_()
        if hasattr(self.ui, "uploadIconbutton"):
            self.ui.uploadIconbutton.raise_()

        old_frame.hide()
        old_frame.deleteLater()

        self.ui.mainBoxcontainer = new_frame

    def open_file_dialog(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.process_and_show_result(file_path)

    def handle_dropped_image(self, file_path):
        self.process_and_show_result(file_path)

    def process_and_show_result(self, file_path):
        self.loading_dialog = LoadingScreen(self)
        self.loading_dialog.show()

        self.worker = PredictionWorker(file_path)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        self.worker.start()

    def on_processing_finished(self, result, file_path):
        if self.loading_dialog is not None:
            self.loading_dialog.close()
            self.loading_dialog = None


        original_image_path = file_path
        predicted_image_path = result.get("image_path")
        node_name = result.get("node_name")
        confidence = result.get("confidence")

        self.result_window = nodeDetailswindow()

        # Put original image
        if original_image_path and hasattr(self.result_window, "set_image_in_frame") and hasattr(self.result_window.ui, "identifiedImageframe"):
            self.result_window.set_image_in_frame(
                self.result_window.ui.identifiedImageframe,
                original_image_path
            )

        # Update result labels if they exist in the details UI
        if hasattr(self.result_window.ui, "resultMainLabel"):
            self.result_window.ui.resultMainLabel.setText(
                node_name if node_name else "No Detection"
            )

        if hasattr(self.result_window.ui, "possibleClassLabel"):
            if confidence is not None:
                self.result_window.ui.possibleClassLabel.setText(
                    f"Confidence: {confidence:.2%}"
                )
            else:
                self.result_window.ui.possibleClassLabel.setText("Confidence: N/A")

        if hasattr(self.result_window.ui, "analysisLabel"):
            self.result_window.ui.analysisLabel.setText("Classified Node Type")

        if hasattr(self.result_window.ui, "resultSubLabel"):
            self.result_window.ui.resultSubLabel.setText("Technology Class")

        self.result_window.show()

    def on_processing_error(self, error_message):
        if self.loading_dialog is not None:
            self.loading_dialog.close()

        QtWidgets.QMessageBox.critical(
            self,
            "Processing Error",
            error_message
        )

    def icon_set(self, widget, icon_path, w, h):
        """
        Set an icon or image on a widget.

        Parameters:
            widget: The target widget. Supported types:
                    - QPushButton: sets button icon
                    - QLabel: sets scaled pixmap
            icon_path (str): Path to the icon/image file
            w (int): Desired width
            h (int): Desired height
        """
        # If the widget is a button, set its icon directly
        if isinstance(widget, QtWidgets.QPushButton):
            icon = QIcon(icon_path)

            if icon.isNull():
                print("Icon not found:", icon_path)
                return

            widget.setStyleSheet("background: transparent; border: none;")
            widget.setAttribute(Qt.WA_TranslucentBackground)
            widget.setIcon(icon)
            widget.setIconSize(QtCore.QSize(w, h))

        # If the widget is a label, load and scale the image as a pixmap
        elif isinstance(widget, QtWidgets.QLabel):
            pixmap = QPixmap(icon_path)

            # Check if the image file was loaded successfully
            if pixmap.isNull():
                print("Image not found:", icon_path)
                return

            # Scale image while preserving aspect ratio and smooth quality
            pixmap = pixmap.scaled(
                w,
                h,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )

            widget.setStyleSheet("background: transparent; border: none;")
            widget.setAttribute(Qt.WA_TranslucentBackground)
            widget.setAutoFillBackground(False)
            widget.setAlignment(Qt.AlignCenter)
            widget.setPixmap(pixmap)
            
            
            
            

    def close_win(self):
        try:
            output_dir = os.path.join(base_dir, "..", "..", "..", "Node_Pipeline", "predicted_images")
            output_dir = os.path.abspath(output_dir)
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
        except Exception:
            pass

        try:
            if self.result_window is not None:
                self.result_window.close()
        except Exception:
            pass

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