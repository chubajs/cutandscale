import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QMessageBox, QHBoxLayout, QProgressBar, QTextEdit
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QImage
from PyQt5.QtCore import Qt, QRect, QPoint, QThread, pyqtSignal, QUrl
from PIL import Image
import io
import os
import asyncio
import fal_client
import base64
import logging
import requests
import tempfile

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ImageLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.line_grab_area = 10  # Pixels on each side of the line that can be grabbed
        self.moving_line = None
        self.line_colors = [
            QColor(255, 0, 0),    # Pure red
            QColor(220, 20, 60),  # Crimson
            QColor(178, 34, 34),  # Firebrick
            QColor(139, 0, 0),    # Dark red
            QColor(255, 69, 0),   # Red-orange
            QColor(255, 99, 71)   # Tomato
        ]

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.parent.display_image and not self.parent.is_cut:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            pixmap = self.pixmap()
            img_rect = pixmap.rect()
            img_rect.moveCenter(self.rect().center())
            
            # Draw lines
            for i, h in enumerate(self.parent.h_lines):
                pen = QPen(self.line_colors[i % len(self.line_colors)])
                pen.setWidth(3)  # Increased width for boldness
                painter.setPen(pen)
                
                y = int(img_rect.top() + h * img_rect.height())
                painter.drawLine(img_rect.left(), y, img_rect.right(), y)

            for i, v in enumerate(self.parent.v_lines):
                pen = QPen(self.line_colors[(i + 3) % len(self.line_colors)])  # Offset by 3 to use different colors
                pen.setWidth(3)  # Increased width for boldness
                painter.setPen(pen)
                
                x = int(img_rect.left() + v * img_rect.width())
                painter.drawLine(x, img_rect.top(), x, img_rect.bottom())

            # Draw coordinates
            for i, h in enumerate(self.parent.h_lines):
                y = int(img_rect.top() + h * img_rect.height())
                y_coord = int(h * self.parent.original_image.height)
                self.draw_coordinate(painter, img_rect.left() + 5, y + 15, f"y: {y_coord}")

            for i, v in enumerate(self.parent.v_lines):
                x = int(img_rect.left() + v * img_rect.width())
                x_coord = int(v * self.parent.original_image.width)
                self.draw_coordinate(painter, x + 5, img_rect.top() + 15, f"x: {x_coord}")

    def draw_coordinate(self, painter, x, y, text):
        # Set up the font
        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)

        # Draw black shadow
        painter.setPen(Qt.black)
        for dx in [-1, 1]:
            for dy in [-1, 1]:
                painter.drawText(x + dx, y + dy, text)

        # Draw white text
        painter.setPen(Qt.white)
        painter.drawText(x, y, text)

    def mousePressEvent(self, event):
        if not self.parent.is_cut and self.parent.display_image:
            pixmap = self.pixmap()
            img_rect = pixmap.rect()
            img_rect.moveCenter(self.rect().center())
            
            if img_rect.contains(event.pos()):
                x = (event.x() - img_rect.left()) / img_rect.width()
                y = (event.y() - img_rect.top()) / img_rect.height()
                
                for i, h in enumerate(self.parent.h_lines):
                    if abs(y - h) * img_rect.height() < self.line_grab_area:
                        self.moving_line = ('h', i)
                        return
                for i, v in enumerate(self.parent.v_lines):
                    if abs(x - v) * img_rect.width() < self.line_grab_area:
                        self.moving_line = ('v', i)
                        return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.parent.is_cut and self.moving_line and self.parent.display_image:
            pixmap = self.pixmap()
            img_rect = pixmap.rect()
            img_rect.moveCenter(self.rect().center())
            
            if img_rect.contains(event.pos()):
                if self.moving_line[0] == 'h':
                    new_y = (event.y() - img_rect.top()) / img_rect.height()
                    self.parent.h_lines[self.moving_line[1]] = max(0, min(1, new_y))
                else:
                    new_x = (event.x() - img_rect.left()) / img_rect.width()
                    self.parent.v_lines[self.moving_line[1]] = max(0, min(1, new_x))
                self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.moving_line = None
        super().mouseReleaseEvent(event)

class UpscaleWorker(QThread):
    progress = pyqtSignal(int, str, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, image_paths, save_path):
        super().__init__()
        self.image_paths = image_paths
        self.save_path = save_path
        self.is_running = True

    def run(self):
        async def upscale_image(img_path, index):
            if not self.is_running:
                return
            try:
                self.log.emit(f"Image {index + 1}: Uploading")
                
                # Upload the image file
                image_url = fal_client.upload_file(img_path)

                self.log.emit(f"Image {index + 1}: Processing")
                response = await fal_client.submit_async("fal-ai/aura-sr", arguments={
                    "image_url": image_url,
                    "upscaling_factor": 4,
                    "checkpoint": "v2"
                })

                result = await response.get()
                upscaled_img_url = result["image"]["url"]
                upscaled_img_path = f"{self.save_path}/upscaled_image_{index+1}.jpg"
                
                self.log.emit(f"Image {index + 1}: Downloading")
                response = requests.get(upscaled_img_url)
                if response.status_code == 200:
                    with open(upscaled_img_path, 'wb') as f:
                        f.write(response.content)
                    self.log.emit(f"Image {index + 1}: Saved")
                else:
                    raise Exception(f"Download failed. Status code: {response.status_code}")

                self.progress.emit(index, upscaled_img_path, "Completed")
            except Exception as e:
                self.log.emit(f"Image {index + 1}: Error - {str(e)}")
                self.error.emit(str(e))
                return False
            return True

        async def upscale_all():
            for i, img_path in enumerate(self.image_paths):
                if not self.is_running:
                    break
                self.progress.emit(i, "", "Starting")
                success = await upscale_image(img_path, i)
                if not success:
                    break

        asyncio.run(upscale_all())
        if self.is_running:
            self.finished.emit()

    def stop(self):
        self.is_running = False
        self.log.emit("Upscale process stopped")

class ImageSplitter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.original_image = None
        self.display_image = None
        self.cut_images = None
        self.h_lines = [0.25, 0.5, 0.75]
        self.v_lines = [0.25, 0.5, 0.75]
        self.line_thickness = 2
        self.last_folder = os.path.expanduser("~")
        self.is_cut = False
        self.upscale_worker = None
        self.current_upscale_index = -1
        self.temp_dir = None

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
        layout.setStretchFactor(self.image_label, 1)  # Make image label expand to fill space

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

        self.upscale_button = QPushButton('Upscale')
        self.upscale_button.clicked.connect(self.upscale_images)
        self.upscale_button.setEnabled(False)
        button_layout.addWidget(self.upscale_button)

        self.stop_upscale_button = QPushButton('Stop Upscale')
        self.stop_upscale_button.clicked.connect(self.stop_upscale)
        self.stop_upscale_button.setEnabled(False)
        button_layout.addWidget(self.stop_upscale_button)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        # Add log text area with fixed height
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setFixedHeight(100)  # Set a fixed height of 100 pixels
        layout.addWidget(self.log_text_edit)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def select_image(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_url, _ = QFileDialog.getOpenFileUrl(
            self,
            "Select Image File",
            QUrl.fromLocalFile(self.last_folder),
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)",
            options=options
        )
        if file_url.isValid():
            file_path = file_url.toLocalFile()
            self.last_folder = os.path.dirname(file_path)
            self.load_image(file_path)

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
            self.update_display_with_highlight()
        elif self.display_image:
            label_size = self.image_label.size()
            scaled_image = self.display_image.copy()
            scaled_image.thumbnail((label_size.width(), label_size.height()), Image.LANCZOS)
            q_image = self.pil_to_qimage(scaled_image)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)
            self.image_label.update()

    def update_display_with_highlight(self):
        if not self.cut_images:
            return

        total_width = sum(img.width for img in self.cut_images[0]) + 5 * (len(self.cut_images[0]) - 1)
        total_height = sum(row[0].height for row in self.cut_images) + 5 * (len(self.cut_images) - 1)
        
        combined = Image.new('RGB', (total_width, total_height), color='white')
        
        y_offset = 0
        image_positions = []
        for row in self.cut_images:
            x_offset = 0
            for img in row:
                combined.paste(img, (x_offset, y_offset))
                image_positions.append((x_offset, y_offset, img.width, img.height))
                x_offset += img.width + 5
            y_offset += row[0].height + 5

        label_width = self.image_label.width()
        label_height = self.image_label.height()

        aspect_ratio = total_width / total_height

        if aspect_ratio > label_width / label_height:
            new_width = label_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = label_height
            new_width = int(new_height * aspect_ratio)

        combined_resized = combined.copy()
        combined_resized.thumbnail((new_width, new_height), Image.LANCZOS)

        scale_factor = new_width / total_width

        q_image = self.pil_to_qimage(combined_resized)
        pixmap = QPixmap.fromImage(q_image)

        if self.current_upscale_index != -1 and self.current_upscale_index < len(image_positions):
            painter = QPainter(pixmap)
            painter.setPen(QPen(Qt.red, 5))
            x, y, width, height = image_positions[self.current_upscale_index]
            scaled_x = int(x * scale_factor)
            scaled_y = int(y * scale_factor)
            scaled_width = int(width * scale_factor)
            scaled_height = int(height * scale_factor)
            painter.drawRect(scaled_x, scaled_y, scaled_width, scaled_height)
            painter.end()

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
        self.upscale_button.setEnabled(True)
        self.update_display()

    def undo_cut(self):
        self.is_cut = False
        self.cut_images = None
        self.undo_button.setEnabled(False)
        self.cut_button.setEnabled(True)
        self.upscale_button.setEnabled(False)
        self.update_display()

    def split_image(self):
        if not self.original_image:
            QMessageBox.warning(self, "Error", "No image loaded. Please select an image first.")
            return

        if self.is_cut:
            images_to_save = [img for row in self.cut_images for img in row]
        else:
            display_width = self.image_label.pixmap().width()
            display_height = self.image_label.pixmap().height()

            width_scale = self.original_image.width / display_width
            height_scale = self.original_image.height / display_height

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

    def upscale_images(self):
        if not self.is_cut or not self.cut_images:
            return

        save_path = QFileDialog.getExistingDirectory(self, "Select Directory to Save Upscaled Images", self.last_folder)
        if not save_path:
            return

        self.last_folder = save_path
        
        # Create a temporary directory to store cut images
        self.temp_dir = tempfile.TemporaryDirectory()
        temp_image_paths = []
        for i, row in enumerate(self.cut_images):
            for j, img in enumerate(row):
                temp_path = os.path.join(self.temp_dir.name, f"temp_image_{i}_{j}.png")
                img.save(temp_path, format="PNG")
                temp_image_paths.append(temp_path)
        
        self.upscale_worker = UpscaleWorker(temp_image_paths, save_path)
        self.upscale_worker.progress.connect(self.update_upscale_progress)
        self.upscale_worker.finished.connect(self.upscale_finished)
        self.upscale_worker.error.connect(self.upscale_error)
        self.upscale_worker.log.connect(self.log_upscale_message)

        self.progress_bar.setMaximum(len(temp_image_paths))
        self.progress_bar.setValue(0)
        self.upscale_button.setEnabled(False)
        self.stop_upscale_button.setEnabled(True)
        
        self.current_upscale_index = 0
        self.update_display_with_highlight()
        
        self.log_text_edit.clear()
        self.log_text_edit.append("Starting upscale process...")
        
        self.upscale_worker.start()

    def stop_upscale(self):
        if self.upscale_worker:
            self.upscale_worker.stop()
            self.stop_upscale_button.setEnabled(False)

    def update_upscale_progress(self, index, upscaled_img_path, status):
        self.progress_bar.setValue(index + 1)
        self.current_upscale_index = index
        if status == "Starting":
            self.log_text_edit.append(f"Starting upscale for image {index + 1}")
        elif status == "Completed":
            self.log_text_edit.append(f"Completed upscale for image {index + 1}")
        self.update_display_with_highlight()

    def upscale_finished(self):
        self.upscale_button.setEnabled(True)
        self.stop_upscale_button.setEnabled(False)
        self.current_upscale_index = -1
        self.update_display()
        self.log_text_edit.append("Upscaling process completed.")
        QMessageBox.information(self, "Success", "Upscaling process completed.")
        if self.temp_dir:
            self.temp_dir.cleanup()
            self.temp_dir = None

    def upscale_error(self, error_message):
        self.log_text_edit.append(f"Error: {error_message}")
        QMessageBox.critical(self, "Error", f"An error occurred during upscaling: {error_message}")
        self.upscale_button.setEnabled(True)
        self.stop_upscale_button.setEnabled(False)
        self.upscale_worker.stop()
        if self.temp_dir:
            self.temp_dir.cleanup()
            self.temp_dir = None

    def log_upscale_message(self, message):
        logging.info(message)
        self.log_text_edit.append(message)
        self.log_text_edit.verticalScrollBar().setValue(
            self.log_text_edit.verticalScrollBar().maximum()
        )

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