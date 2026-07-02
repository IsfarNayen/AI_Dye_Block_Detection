from PIL import Image, ImageDraw, ImageFont, ImageFilter
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QDesktopServices


class SaveSegmentedImage:
    def __init__(self, segmented_image_path, all_details, open_file_dialog_func):
        self.segmented_image_path = segmented_image_path
        self.all_details = all_details
        self.open_file_dialog = open_file_dialog_func

    def save(self):
        source = self.segmented_image_path
        dest = self.open_file_dialog()

        if not dest:
            return

        # -----------------------------
        # Open segmented image
        # -----------------------------
        seg_img = Image.open(source).convert("RGBA")

        # -----------------------------
        # Convert dataframe into [(name, rgb), ...]
        # -----------------------------
        labels = []
        for _, row in self.all_details.iterrows():
            name = str(row["class_name"])
            color = row["class_color_rgb"]
            ratio = row["ratio_percent"]

            if isinstance(color, str):
                color = color.strip().strip("()")
                color = tuple(int(c.strip()) for c in color.split(","))

            try:
                ratio = float(ratio)
                label_text = f"{name} (Area: {ratio:.2f}%)"
            except Exception:
                label_text = f"{name} (Area: {ratio}%)"

            labels.append((label_text, tuple(color)))

        # -----------------------------
        # Fonts
        # -----------------------------
        title_font = self.load_font(34, bold=True)
        legend_title_font = self.load_font(20, bold=True)
        text_font = self.load_font(18, bold=False)

        # -----------------------------
        # Layout configuration
        # -----------------------------
        outer_margin = 28
        inner_gap = 26
        top_header_h = 110

        legend_box_w = 300
        legend_item_gap = 22
        legend_color_size = 24
        legend_left_pad = 28
        legend_top_pad = 90
        legend_bottom_pad = 30

        image_card_pad = 18

        # -----------------------------
        # Legend dynamic height
        # -----------------------------
        legend_content_h = len(labels) * (legend_color_size + legend_item_gap)
        legend_box_h = legend_top_pad + legend_content_h + legend_bottom_pad
        legend_box_h = max(legend_box_h, 420)

        # -----------------------------
        # Scale image
        # -----------------------------
        max_display_w = 900
        max_display_h = 700
        min_display_w = 500
        min_display_h = 400
        max_upscale = 3.0

        fit_ratio = min(max_display_w / seg_img.width, max_display_h / seg_img.height)

        # Only zoom if image is smaller than desired minimum view size
        if seg_img.width < min_display_w or seg_img.height < min_display_h:
            zoom_ratio = min(min_display_w / seg_img.width, min_display_h / seg_img.height)
            scale_ratio = min(max(fit_ratio, zoom_ratio), max_upscale)
        else:
            scale_ratio = min(fit_ratio, 1.0) if (seg_img.width > max_display_w or seg_img.height > max_display_h) else 1.0

        scaled_w = int(seg_img.width * scale_ratio)
        scaled_h = int(seg_img.height * scale_ratio)

        seg_img = seg_img.resize((scaled_w, scaled_h), Image.LANCZOS)

        # -----------------------------
        # Dynamic image frame size
        # -----------------------------
        min_card_w = 260
        min_card_h = 260

        image_card_w = max(min_card_w, scaled_w + image_card_pad * 2)
        image_card_h = max(min_card_h, scaled_h + image_card_pad * 2)

        # Content height should fit both legend and image
        content_h = max(legend_box_h, image_card_h)

        canvas_w = outer_margin + legend_box_w + inner_gap + image_card_w + outer_margin
        canvas_h = top_header_h + content_h + outer_margin

        # -----------------------------
        # Main canvas
        # -----------------------------
        bg = Image.new("RGBA", (canvas_w, canvas_h), (244, 247, 248, 255))
        draw = ImageDraw.Draw(bg)

        # Outer panel
        draw.rounded_rectangle(
            (10, 10, canvas_w - 10, canvas_h - 10),
            radius=28,
            fill=(248, 250, 251, 255),
            outline=(143, 151, 200),
            width=2
        )

        # -----------------------------
        # Header title
        # -----------------------------
        title_text = "SEGMENTED IMAGE"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_w = title_bbox[2] - title_bbox[0]
        title_h = title_bbox[3] - title_bbox[1]

        title_box_w = max(430, title_w + 90)
        title_box_h = 62

        title_x1 = (canvas_w - title_box_w) // 2
        title_y1 = 24
        title_x2 = title_x1 + title_box_w
        title_y2 = title_y1 + title_box_h

        draw.rounded_rectangle(
            (title_x1, title_y1, title_x2, title_y2),
            radius=20,
            fill=(143, 151, 200)
        )

        draw.text(
            ((canvas_w - title_w) // 2, title_y1 + (title_box_h - title_h) // 2 - 3),
            title_text,
            fill=(255, 255, 255, 255),
            font=title_font
        )

        line_y = title_y1 + title_box_h // 2
        draw.line((100, line_y, title_x1 - 30, line_y), fill=(143, 151, 200), width=2)
        draw.line((title_x2 + 30, line_y, canvas_w - 100, line_y), fill=(143, 151, 200), width=2)

        # -----------------------------
        # Positions
        # -----------------------------
        content_top = top_header_h
        legend_x1 = outer_margin
        legend_y1 = content_top + (content_h - legend_box_h) // 2
        legend_x2 = legend_x1 + legend_box_w
        legend_y2 = legend_y1 + legend_box_h

        image_x1 = legend_x2 + inner_gap
        image_y1 = content_top + (content_h - image_card_h) // 2
        image_x2 = image_x1 + image_card_w
        image_y2 = image_y1 + image_card_h

        # Shadows
        bg = self.add_shadow(bg, (legend_x1, legend_y1, legend_x2, legend_y2), radius=24)
        bg = self.add_shadow(bg, (image_x1, image_y1, image_x2, image_y2), radius=24)
        draw = ImageDraw.Draw(bg)

        # -----------------------------
        # Legend card
        # -----------------------------
        draw.rounded_rectangle(
            (legend_x1, legend_y1, legend_x2, legend_y2),
            radius=24,
            fill=(255, 255, 255, 255),
            outline=(215, 225, 228, 255),
            width=2
        )

        legend_header_text = "LEGEND"
        legend_header_bbox = draw.textbbox((0, 0), legend_header_text, font=legend_title_font)
        legend_header_w = legend_header_bbox[2] - legend_header_bbox[0]
        legend_header_h = legend_header_bbox[3] - legend_header_bbox[1]

        legend_pill_w = max(150, legend_header_w + 60)
        legend_pill_h = 36
        legend_pill_x1 = legend_x1 + (legend_box_w - legend_pill_w) // 2
        legend_pill_y1 = legend_y1 + 26
        legend_pill_x2 = legend_pill_x1 + legend_pill_w
        legend_pill_y2 = legend_pill_y1 + legend_pill_h

        draw.rounded_rectangle(
            (legend_pill_x1, legend_pill_y1, legend_pill_x2, legend_pill_y2),
            radius=14,
            fill=(143, 151, 200)
        )

        draw.text(
            (
                legend_pill_x1 + (legend_pill_w - legend_header_w) // 2,
                legend_pill_y1 + (legend_pill_h - legend_header_h) // 2 - 2
            ),
            legend_header_text,
            fill=(255, 255, 255, 255),
            font=legend_title_font
        )

        yy = legend_y1 + legend_top_pad
        for name, color in labels:
            draw.rounded_rectangle(
                (
                    legend_x1 + legend_left_pad,
                    yy,
                    legend_x1 + legend_left_pad + legend_color_size,
                    yy + legend_color_size
                ),
                radius=5,
                fill=color,
                outline=(120, 120, 120, 255),
                width=1
            )

            text_bbox = draw.textbbox((0, 0), name, font=text_font)
            text_h = text_bbox[3] - text_bbox[1]

            draw.text(
                (
                    legend_x1 + legend_left_pad + legend_color_size + 16,
                    yy + (legend_color_size - text_h) // 2 - 1
                ),
                name,
                fill=(40, 40, 40, 255),
                font=text_font
            )

            yy += legend_color_size + legend_item_gap

        # -----------------------------
        # Image card
        # -----------------------------
        draw.rounded_rectangle(
            (image_x1, image_y1, image_x2, image_y2),
            radius=24,
            fill=(255, 255, 255, 255),
            outline=(215, 225, 228, 255),
            width=2
        )

        paste_x = image_x1 + (image_card_w - seg_img.width) // 2
        paste_y = image_y1 + (image_card_h - seg_img.height) // 2
        bg.paste(seg_img, (paste_x, paste_y), seg_img)

        # -----------------------------
        # Save and ask to open
        # -----------------------------
        final_img = bg.convert("RGB")
        final_img.save(dest, quality=95)

        self.ask_to_open_image(dest)


    
    def ask_to_open_image(self, file_path):
        dialog = QtWidgets.QDialog()
        dialog.setFixedSize(420, 220)
        dialog.setModal(True)
        dialog.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        dialog.setWindowFlags(
            QtCore.Qt.Dialog |
            QtCore.Qt.FramelessWindowHint
        )



        main_frame = QtWidgets.QFrame(dialog)
        main_frame.setObjectName("mainFrame")
        main_frame.setGeometry(0, 0, 420, 220)
        
        
        
        main_frame.setStyleSheet("""
            QFrame#mainFrame {
                background-color: rgb(248, 250, 251);
                border: 2px solid rgb(143, 151, 200);
                border-radius: 18px;
            }

            QLabel {
                color: rgb(40, 40, 40);
                font-size: 16px;
                font-weight: 600;
                background: transparent;
                
            }

            QPushButton {
                background-color: rgb(143, 151, 200);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 600;
                min-width: 110px;
            }

            QPushButton:hover {
                background-color: rgb(123, 132, 185);
            }

            QPushButton:pressed {
                background-color: rgb(105, 114, 170);
            }

            QPushButton#cancelBtn {
                background-color: white;
                color: rgb(80, 80, 80);
                border: 1px solid rgb(210, 215, 225);
            }

            QPushButton#cancelBtn:hover {
                background-color: rgb(242, 244, 248);
            }
        """)

        layout = QtWidgets.QVBoxLayout(main_frame)
        layout.setContentsMargins(25, 25, 25, 20)
        layout.setSpacing(18)

        title = QtWidgets.QLabel("Image saved successfully.")
        title.setAlignment(QtCore.Qt.AlignCenter)

        msg = QtWidgets.QLabel("Do you want to open the saved image?")
        msg.setAlignment(QtCore.Qt.AlignCenter)
        msg.setWordWrap(True)
        msg.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 400;
                color: rgb(70,70,70);
            }
        """)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(14)

        open_btn = QtWidgets.QPushButton("Open Image")
        cancel_btn = QtWidgets.QPushButton("Not Now")
        cancel_btn.setObjectName("cancelBtn")

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(open_btn)
        btn_layout.addStretch()

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(msg)
        layout.addStretch()
        layout.addLayout(btn_layout)

        open_btn.clicked.connect(
            lambda: (
                QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(file_path)),
                dialog.accept()
            )
        )

        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec_()
    
    

    def load_font(self, size, bold=False):
        if bold:
            font_candidates = [
                "arialbd.ttf",
                "Arial Bold.ttf",
                "DejaVuSans-Bold.ttf"
            ]
        else:
            font_candidates = [
                "arial.ttf",
                "Arial.ttf",
                "DejaVuSans.ttf"
            ]

        for font_name in font_candidates:
            try:
                return ImageFont.truetype(font_name, size)
            except Exception:
                continue

        return ImageFont.load_default()


    def add_shadow(self, base_img, box, radius=22, offset=(6, 8), shadow_alpha=55):
        shadow = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)

        sx1, sy1, sx2, sy2 = box
        ox, oy = offset

        shadow_draw.rounded_rectangle(
            (sx1 + ox, sy1 + oy, sx2 + ox, sy2 + oy),
            radius=radius,
            fill=(0, 0, 0, shadow_alpha)
        )

        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        return Image.alpha_composite(base_img, shadow)