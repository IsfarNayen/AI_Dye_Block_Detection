from PyQt5 import QtCore, QtWidgets
import os
import shutil
from backend import SegmentationBackend
backend = SegmentationBackend()
backend.load_models()


class PredictionWorker(QtCore.QThread):
    finished = QtCore.pyqtSignal(dict, str)
    error = QtCore.pyqtSignal(str)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path

    def run(self):
        try:
            result = backend.predict_image_from_gui(self.file_path)
            self.finished.emit(result, self.file_path)
        except Exception as e:
            self.error.emit(str(e))