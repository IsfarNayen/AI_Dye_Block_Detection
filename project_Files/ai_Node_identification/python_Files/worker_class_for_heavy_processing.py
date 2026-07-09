from PyQt5 import QtCore
from .backend_pipeline import pipeline


class PredictionWorker(QtCore.QThread):
    finished = QtCore.pyqtSignal(dict, str)
    error = QtCore.pyqtSignal(str)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path

    def run(self):
        try:
            # Run backend pipeline on the selected image
            result = pipeline(self.file_path)

            # Send result back to main UI
            self.finished.emit(result, self.file_path)

        except Exception as e:
            self.error.emit(str(e))