import sys
import os
import shutil, subprocess
from pathlib import Path

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QIcon

from ..UI.skeleton_UI_files.main_ui import Ui_MainWindow

# Absolute path of the current file's directory.
# This is useful when building paths relative to this script.
base_dir = os.path.dirname(os.path.abspath(__file__))


class MainApp(QtWidgets.QMainWindow):
    """
    Main landing page window for the application.

    This window provides navigation to different projects/modules,
    such as Block Segmentation and Node Identification.

    Features:
    - Frameless custom window
    - Manual drag support
    - Open child project windows
    - Disable navigation buttons while child window is open
    """

    def __init__(self):
        """
        Initialize the landing page window, set up the UI,
        configure frameless window behavior, and connect button signals.
        """
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setFixedSize(self.size())
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        
        # --------------------------- Placing images in the placeholder of widgets in landing page ------------------------------
        self.icon_set(self.ui.blockSegiconlabel, os.path.join( base_dir, "..", "..", "..", "asset", "Landing_Page_Block_Segmentation_big_icon.png"), 120, 120)
        self.icon_set(self.ui.nodeIdentiiconlabel, os.path.join( base_dir, "..", "..", "..", "asset", "Landing_Page_node_identification_big_icon.png"), 120, 120)
        self.icon_set(self.ui.appIconLabel, os.path.join( base_dir, "..", "..", "..", "asset", "app_logo.png"), 100, 100)
        self.icon_set(self.ui.logoPushbutton, os.path.join( base_dir, "..", "..", "..", "asset", "app_logo_small.png"), 32, 32)
        

        
        # --------------------------- Declaring variable for identification and segmentation project ----------------------------
        self.identification_process = None
        self.segmentation_process = None

        self._drag_active = False
        self._drag_position = QPoint()

        self.ui.closeButton.clicked.connect(self.close_win)
        self.ui.minimizeButton.clicked.connect(self.showMinimized)
        self.ui.blockSegOpenButton.clicked.connect(self.open_Block_segmentation_project)
        self.ui.nodeIdentiOpenButton.clicked.connect(self.open_Node_identification_project)




    # -------------------------- Block Segmentation Opening & Closing Part -----------------------
    def open_Block_segmentation_project(self):
        """
        Open the Block Segmentation project window using QProcess.
        """
        self.segmentation_process = QtCore.QProcess(self)
        self.segmentation_process.finished.connect(self.on_block_segmentation_finished)

        project_root = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))
        self.segmentation_process.setWorkingDirectory(project_root)

        self.enable_buttons(False)

        self.segmentation_process.start(
            sys.executable,
            ["-m", "project_Files.ai_Dye_segmentation.python_Files.main"]
        )


    def on_block_segmentation_finished(self):
        self.segmentation_process = None
        self.enable_buttons(True)



    # -------------------------- Node Identification Opening & Closing Part -----------------------
    def open_Node_identification_project(self):
        """
        Open the Node Identification project window using QProcess.
        """
        self.identification_process = QtCore.QProcess(self)
        self.identification_process.finished.connect(self.on_node_identification_finished)

        project_root = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))
        self.identification_process.setWorkingDirectory(project_root)

        self.enable_buttons(False)

        self.identification_process.start(
            sys.executable,
            ["-m", "project_Files.ai_Node_identification.python_Files.main"]
        )


    def on_node_identification_finished(self):
        self.identification_process = None
        self.enable_buttons(True)


    # -------------------------- Enables the project opening button in the fronntend -----------------------
    def enable_buttons(self, flag):
        """
        Enable/Disable landing page project buttons.
        """
        self.ui.blockSegOpenButton.setEnabled(flag)
        self.ui.nodeIdentiOpenButton.setEnabled(flag)


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
        """
        Close the application window safely.

        Notes:
        - Optionally removes the outputs folder if needed
        - Closes result window if it exists
        - Finally closes all application windows
        """
        # Try removing outputs folder safely
        self.remove_folders()


        " Closes all the windows under the parent window "
        try:
            if hasattr(self, "result_window") and self.result_window is not None:
                self.result_window.close()
        except Exception:
            pass

        # Close all windows in the application
        QtWidgets.QApplication.closeAllWindows()
    

    
    def remove_folders(self):
        " Removes the output folders of all projects "
        # Try removing outputs folder safely
        project_dir = Path("models")
        project_list = [folder_name.name for folder_name in project_dir.iterdir() if folder_name.is_dir()]

        
        for project_name in project_list:
            try:
                output_path = os.path.join("." , "models" , project_name , "outputs")
                if os.path.exists(output_path):
                    shutil.rmtree(output_path)
            except Exception as e:
                pass
    
    
    def mousePressEvent(self, event):
        """
        Handle mouse press event for dragging the frameless window.

        Starts dragging when the left mouse button is pressed.
        """
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """
        Handle mouse move event for dragging the frameless window.

        Moves the window while the left mouse button is pressed.
        """
        if self._drag_active and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release event for dragging.

        Stops dragging when the mouse button is released.
        """
        self._drag_active = False
        event.accept()


if __name__ == "__main__":
    """
    Application entry point.

    Creates the QApplication, launches the main landing page,
    and starts the Qt event loop.
    """
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())