# segmented_details_main.py
import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from segmented_details import Ui_MainWindow


class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._drag_active = False
        self._drag_position = QtCore.QPoint()

        self._setup_connections()

    def _setup_connections(self):
        self.ui.closePushbutton.clicked.connect(self.close)


    def set_result_data(self, original_image_path, segmented_image_path, details_df, area_summary=None):
        self.set_image_in_frame(self.ui.originalImageframe, original_image_path)
        self.set_image_in_frame(self.ui.segmentedImageframe, segmented_image_path)
        self.populate_details(details_df, area_summary)

    def set_image_in_frame(self, frame, image_path):
        # remove previous layout/widgets if any
        old_layout = frame.layout()
        if old_layout is not None:
            while old_layout.count():
                item = old_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            QtWidgets.QWidget().setLayout(old_layout)

        label = QtWidgets.QLabel(frame)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("background: transparent; border: none;")

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            label.setText("Image not found")
        else:
            scaled = pixmap.scaled(
                frame.width() - 16,
                frame.height() - 16,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            label.setPixmap(scaled)

        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(label)

    def populate_details(self, details_df, area_summary=None):
        container = self.ui.scrollAreaWidgetContents

        # Clear old layout safely
        old_layout = container.layout()
        if old_layout is not None:
            while old_layout.count():
                item = old_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            QtWidgets.QWidget().setLayout(old_layout)

        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Optional summary
        if area_summary:
            summary_label = QtWidgets.QLabel(str(area_summary))
            summary_label.setWordWrap(True)
            summary_label.setStyleSheet("""
                QLabel {
                    background: rgba(255,255,255,0.35);
                    border: 1px solid rgba(255,255,255,0.55);
                    border-radius: 10px;
                    padding: 10px;
                    color: #5d5e70;
                    font-size: 13px;
                    font-weight: 500;
                }
            """)
            layout.addWidget(summary_label)

        # 🔥 Main loop
        for _, row in details_df.iterrows():
            class_name = str(row["class_name"])
            ratio_percent = float(row["ratio_percent"])
            hex_color = str(row["class_color_hex"])   # ✅ Direct use

            # Card container
            card = QtWidgets.QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: rgba(255,255,255,0.40);
                    border: 1px solid rgba(255,255,255,0.55);
                    border-radius: 12px;
                }
                QLabel {
                    background: transparent;
                    border: none;
                    color: #5f6172;
                    font-size: 13px;
                }
            """)

            card_layout = QtWidgets.QHBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            card_layout.setSpacing(10)

            # 🎨 Color box
            color_box = QtWidgets.QLabel()
            color_box.setFixedSize(18, 18)
            color_box.setStyleSheet(f"""
                QLabel {{
                    background-color: {hex_color};
                    border: 1px solid rgba(95, 97, 114, 0.25);
                    border-radius: 5px;
                }}
            """)

            # Labels
            name_label = QtWidgets.QLabel(class_name)
            # hex_label = QtWidgets.QLabel(hex_color)
            value_label = QtWidgets.QLabel(f"Area Percentage: {ratio_percent:.2f}%")

            # hex_label.setStyleSheet("""
            #     QLabel {
            #         color: #7c7f96;
            #         font-size: 12px;
            #         font-weight: 500;
            #     }
            # """)

            # Left group (color + name + hex)
            left_layout = QtWidgets.QHBoxLayout()
            left_layout.setSpacing(8)
            left_layout.addWidget(color_box)
            left_layout.addWidget(name_label)
            # left_layout.addWidget(hex_label)

            left_widget = QtWidgets.QWidget()
            left_widget.setLayout(left_layout)

            # Add to card
            card_layout.addWidget(left_widget, 2)
            card_layout.addWidget(value_label, 1)

            layout.addWidget(card)

        layout.addStretch()



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


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()