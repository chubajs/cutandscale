import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QMessageBox, QHBoxLayout
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QImage
from PyQt5.QtCore import Qt, QRect, QPoint
from PIL import Image
import io
import os

class ImageLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.parent.display_image and not self.parent.is_cut:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw the lines over the image
            pen = QPen(QColor(255, 0, 0, 128))  # Semi-transparent red
            painter.setPen(pen)
            
            # Get the actual image dimensions and position within the label
            pixmap = self.pixmap()
            img_rect = pixmap.rect()
            img_rect.moveCenter(self.rect().center())
            
            # Draw 3 horizontal lines with coordinates
            for h in self.parent.h_lines:
                y = int(img_rect.top() + h * img_rect.height())
                painter.drawLine(img_rect.left(), y, img_rect.right(), y)
                y_coord = int(h * self.parent.original_image.height)
                painter.drawText(img_rect.left() + 5, y + 15, f"y: {y_coord}")

            # Draw 3 vertical lines with coordinates
            for v in self.parent.v_lines:
                x = int(img_rect.left() + v * img_rect.width())
                painter.drawLine(x, img_rect.top(), x, img_rect.bottom())
                x_coord = int(v * self.parent.original_image.width)
                painter.drawText(x + 5, img_rect.top() + 15, f"x: {x_coord}")

class ImageSplitter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.original_image = None
        self.display_image = None
        self.cut_images = None
        self.h_lines = [0.25, 0.5, 0.75]
        self.v_lines = [0.25, 0.5, 0.75]
        self.moving_line = None
        self.line_thickness = 2
        self.last_folder = os.path.expanduser("~")
        self.is_cut = False

    def initUI(self):
        self.setWindowTitle('Image Splitter')
        self.setGeometry(100, 100, 1000, 800)

        layout = QVBoxLayout()

        self.select_button = QPushButton('Select Image')
        self.select_button.clicked.connect(self.select_image)
        layout.addWidget(self.select_button)

        self.image_label = ImageLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        button_layout = QHBoxLayout()

        self.cut_button = QPushButton('Cut')
        self.cut_button.clicked.connect(self.cut_image)
        self.cut_button.setEnabled(False)
        button_layout.addWidget(self.cut_button)

        self.undo_button = QPushButton('Undo')
        self.undo_button.clicked.connect(self.undo_cut)
        self.undo_button.setEnabled(False)
        button_layout.addWidget(self.undo_button)

        self.split_button = QPushButton('Save')
        self.split_button.clicked.connect(self.split_image)
        self.split_button.setEnabled(False)
        button_layout.addWidget(self.split_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def select_image(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Image File", self.last_folder, "Image Files (*.png *.jpg *.bmp)", options=options)
        if file_name:
            self.last_folder = os.path.dirname(file_name)
            self.load_image(file_name)

    def load_image(self, file_path):
        try:
            self.original_image = Image.open(file_path)
            self.display_image = self.original_image.copy()
            self.display_image.thumbnail((900, 700))
            self.update_display()
            self.cut_button.setEnabled(True)
            self.split_button.setEnabled(True)
            self.is_cut = False
        except Exception as e:
            print(f"Error loading image: {e}")

    def update_display(self):
        if self.is_cut and self.cut_images:
            self.display_cut_images()
        elif self.display_image:
            # Resize the display image to fit the label
            label_size = self.image_label.size()
            scaled_image = self.display_image.copy()
            scaled_image.thumbnail((label_size.width(), label_size.height()), Image.LANCZOS)
            q_image = self.pil_to_qimage(scaled_image)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)
            self.image_label.update()

    def display_cut_images(self):
        if not self.cut_images:
            return

        # Calculate the total width and height of the combined image
        total_width = sum(img.width for img in self.cut_images[0]) + 5 * (len(self.cut_images[0]) - 1)
        total_height = sum(row[0].height for row in self.cut_images) + 5 * (len(self.cut_images) - 1)
        
        # Create a new image with the calculated dimensions
        combined = Image.new('RGB', (total_width, total_height), color='white')
        
        # Paste the cut images onto the combined image
        y_offset = 0
        for row in self.cut_images:
            x_offset = 0
            for img in row:
                combined.paste(img, (x_offset, y_offset))
                x_offset += img.width + 5
            y_offset += row[0].height + 5

        # Calculate the aspect ratio of the combined image
        aspect_ratio = total_width / total_height

        # Get the size of the label
        label_width = self.image_label.width()
        label_height = self.image_label.height()

        # Calculate the size to fit the combined image within the label
        if aspect_ratio > label_width / label_height:
            # Width constrained
            new_width = label_width
            new_height = int(new_width / aspect_ratio)
        else:
            # Height constrained
            new_height = label_height
            new_width = int(new_height * aspect_ratio)

        # Resize the combined image to fit within the label
        combined_resized = combined.copy()
        combined_resized.thumbnail((new_width, new_height), Image.LANCZOS)

        # Convert to QPixmap and display
        q_image = self.pil_to_qimage(combined_resized)
        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)
        self.image_label.update()

    def cut_image(self):
        if not self.original_image:
            return

        h_pixels = [0] + [int(h * self.original_image.height) for h in self.h_lines] + [self.original_image.height]
        v_pixels = [0] + [int(v * self.original_image.width) for v in self.v_lines] + [self.original_image.width]

        self.cut_images = []
        for i in range(len(h_pixels) - 1):
            row = []
            for j in range(len(v_pixels) - 1):
                left, upper, right, lower = v_pixels[j], h_pixels[i], v_pixels[j+1], h_pixels[i+1]
                img = self.original_image.crop((left, upper, right, lower))
                row.append(img)
            self.cut_images.append(row)

        self.is_cut = True
        self.undo_button.setEnabled(True)
        self.cut_button.setEnabled(False)
        self.update_display()

    def undo_cut(self):
        self.is_cut = False
        self.cut_images = None
        self.undo_button.setEnabled(False)
        self.cut_button.setEnabled(True)
        self.update_display()

    def mousePressEvent(self, event):
        if not self.is_cut and self.display_image:
            image_rect = self.image_label.geometry()
            if image_rect.contains(event.pos()):
                x = (event.x() - image_rect.left()) / image_rect.width()
                y = (event.y() - image_rect.top()) / image_rect.height()
                
                for i, h in enumerate(self.h_lines):
                    if abs(y - h) < 0.02:
                        self.moving_line = ('h', i)
                        return
                for i, v in enumerate(self.v_lines):
                    if abs(x - v) < 0.02:
                        self.moving_line = ('v', i)
                        return

    def mouseMoveEvent(self, event):
        if not self.is_cut and self.moving_line and self.display_image:
            image_rect = self.image_label.geometry()
            if image_rect.contains(event.pos()):
                if self.moving_line[0] == 'h':
                    new_y = (event.y() - image_rect.top()) / image_rect.height()
                    self.h_lines[self.moving_line[1]] = max(0, min(1, new_y))
                else:
                    new_x = (event.x() - image_rect.left()) / image_rect.width()
                    self.v_lines[self.moving_line[1]] = max(0, min(1, new_x))
                self.image_label.update()
                # Removed the print_coordinates() call

    def mouseReleaseEvent(self, event):
        self.moving_line = None

    def split_image(self):
        if not self.original_image:
            QMessageBox.warning(self, "Error", "No image loaded. Please select an image first.")
            return

        if self.is_cut:
            images_to_save = [img for row in self.cut_images for img in row]
        else:
            # Get the current dimensions of the displayed image
            display_width = self.image_label.pixmap().width()
            display_height = self.image_label.pixmap().height()

            # Calculate the scaling factors
            width_scale = self.original_image.width / display_width
            height_scale = self.original_image.height / display_height

            # Calculate pixel positions based on the original image size
            h_pixels = [0] + [int(h * display_height * height_scale) for h in self.h_lines] + [self.original_image.height]
            v_pixels = [0] + [int(v * display_width * width_scale) for v in self.v_lines] + [self.original_image.width]

            images_to_save = []
            for i in range(len(h_pixels) - 1):
                for j in range(len(v_pixels) - 1):
                    left = v_pixels[j]
                    upper = h_pixels[i]
                    right = v_pixels[j+1]
                    lower = h_pixels[i+1]
                    img = self.original_image.crop((left, upper, right, lower))
                    images_to_save.append(img)

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        save_path = QFileDialog.getExistingDirectory(self, "Select Directory to Save Images", self.last_folder, options=options)
        if save_path:
            self.last_folder = save_path
            try:
                for i, img in enumerate(images_to_save):
                    img.save(f"{save_path}/split_image_{i+1}.jpg", quality=100, subsampling=0)
                
                success_message = f"Images successfully saved to {save_path}"
                print(success_message)
                QMessageBox.information(self, "Success", success_message)
            except Exception as e:
                error_message = f"Error saving images: {str(e)}"
                print(error_message)
                QMessageBox.critical(self, "Error", error_message)
        else:
            print("Image splitting cancelled.")

    def pil_to_qimage(self, pil_image):
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        q_image = QImage()
        q_image.loadFromData(buffer.getvalue())
        return q_image

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageSplitter()
    ex.show()
    sys.exit(app.exec_())