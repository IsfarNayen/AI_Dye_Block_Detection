from PyQt5 import QtWidgets, QtCore
import os

class DragDropFrame(QtWidgets.QFrame):
    fileDropped = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.set_normal_style()

    def set_normal_style(self):
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.34),
                    stop:1 rgba(255,255,255,0.20)
                );
                border: 2px dashed #d3cede;
                border-radius: 22px;
            }
        """)

    def set_hover_style(self):
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(180,190,240,0.35),
                    stop:1 rgba(255,255,255,0.28)
                );
                border: 2px dashed #8f9ad8;
                border-radius: 22px;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    event.acceptProposedAction()
                    self.set_hover_style()
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.set_normal_style()
        event.accept()

    def dropEvent(self, event):
        self.set_normal_style()
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    self.fileDropped.emit(file_path)
                    event.acceptProposedAction()
                    return
        event.ignore()