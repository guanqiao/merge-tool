"""
Image comparison widget for displaying and comparing image files.

Provides side-by-side image comparison with overlay mode and pixel-level diff highlighting.
"""

import logging
logger = logging.getLogger("MergeDiffTool.ImageDiffView")

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
    QPushButton, QFileDialog, QMessageBox, QSlider,
    QCheckBox, QComboBox, QSplitter, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QPoint, QRectF
from PySide6.QtGui import (
    QImage, QPixmap, QPainter, QColor, QMouseEvent,
    QWheelEvent, QResizeEvent, QPen, QBrush
)
from typing import Optional, Tuple
import os


class ImageLabel(QLabel):
    """Custom label for displaying images with zoom and pan support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = None
        self._pixmap = None
        self._scale_factor = 1.0
        self._offset_x = 0
        self._offset_y = 0
        self._last_mouse_pos = QPoint()
        self._dragging = False
        self._diff_mask = None
        self._show_diff = False
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setStyleSheet("background-color: #2d2d2d; border: 1px solid #444;")

    def set_image(self, image: QImage):
        """Set the image to display."""
        self._image = image
        self._update_pixmap()

    def get_image(self) -> Optional[QImage]:
        """Get the current image."""
        return self._image

    def set_diff_mask(self, mask: QImage):
        """Set the difference mask to overlay."""
        self._diff_mask = mask
        self._update_pixmap()

    def set_show_diff(self, show: bool):
        """Toggle diff overlay display."""
        self._show_diff = show
        self._update_pixmap()

    def set_scale(self, scale: float):
        """Set the zoom scale factor."""
        self._scale_factor = max(0.1, min(10.0, scale))
        self._update_pixmap()

    def get_scale(self) -> float:
        """Get the current scale factor."""
        return self._scale_factor

    def reset_view(self):
        """Reset zoom and pan to default."""
        self._scale_factor = 1.0
        self._offset_x = 0
        self._offset_y = 0
        self._update_pixmap()

    def _update_pixmap(self):
        """Update the displayed pixmap."""
        if not self._image:
            self.clear()
            return

        if self._show_diff and self._diff_mask:
            combined = QImage(self._image.size(), QImage.Format_ARGB32)
            painter = QPainter(combined)
            painter.drawImage(0, 0, self._image)
            painter.setCompositionMode(QPainter.CompositionMode_Multiply)
            painter.drawImage(0, 0, self._diff_mask)
            painter.end()
            source = combined
        else:
            source = self._image

        scaled_size = source.size() * self._scale_factor
        scaled_image = source.scaled(
            scaled_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self._pixmap = QPixmap.fromImage(scaled_image)
        self.setPixmap(self._pixmap)
        self.adjustSize()

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events for panning."""
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events for panning."""
        if self._dragging:
            delta = event.pos() - self._last_mouse_pos
            self._offset_x += delta.x()
            self._offset_y += delta.y()
            self._last_mouse_pos = event.pos()
            self.move(self._offset_x, self._offset_y)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event: QWheelEvent):
        """Handle wheel events for zooming."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.set_scale(self._scale_factor * 1.1)
        else:
            self.set_scale(self._scale_factor / 1.1)


class ImageDiffView(QWidget):
    """Widget for displaying and comparing image files."""

    file_loaded = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("ImageDiffView.__init__ called")
        self._left_file_path = None
        self._right_file_path = None
        self._left_image = None
        self._right_image = None
        self._overlay_mode = False
        self._diff_threshold = 10

        logger.debug("Calling _setup_ui...")
        self._setup_ui()
        logger.debug("ImageDiffView initialization complete")

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)

        self.btn_open_left = QPushButton("Open Left...")
        self.btn_open_right = QPushButton("Open Right...")
        self.btn_overlay = QPushButton("Overlay Mode")
        self.btn_overlay.setCheckable(True)
        self.btn_diff = QPushButton("Show Differences")
        self.btn_diff.setCheckable(True)
        self.btn_reset = QPushButton("Reset View")

        toolbar_layout.addWidget(QLabel("Zoom:"))
        self.slider_zoom = QSlider(Qt.Horizontal)
        self.slider_zoom.setRange(10, 500)
        self.slider_zoom.setValue(100)
        self.slider_zoom.setFixedWidth(150)
        toolbar_layout.addWidget(self.slider_zoom)

        toolbar_layout.addWidget(QLabel("Diff Threshold:"))
        self.slider_threshold = QSlider(Qt.Horizontal)
        self.slider_threshold.setRange(0, 255)
        self.slider_threshold.setValue(10)
        self.slider_threshold.setFixedWidth(150)
        toolbar_layout.addWidget(self.slider_threshold)

        toolbar_layout.addWidget(self.btn_open_left)
        toolbar_layout.addWidget(self.btn_open_right)
        toolbar_layout.addWidget(self.btn_overlay)
        toolbar_layout.addWidget(self.btn_diff)
        toolbar_layout.addWidget(self.btn_reset)

        layout.addWidget(toolbar)

        main_splitter = QSplitter(Qt.Horizontal)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_label = QLabel("Left Image")
        left_label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.left_scroll = QScrollArea()
        self.left_scroll.setWidgetResizable(True)
        self.left_image_label = ImageLabel()
        self.left_scroll.setWidget(self.left_image_label)
        left_layout.addWidget(left_label)
        left_layout.addWidget(self.left_scroll)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_label = QLabel("Right Image")
        right_label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.right_scroll = QScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_image_label = ImageLabel()
        self.right_scroll.setWidget(self.right_image_label)
        right_layout.addWidget(right_label)
        right_layout.addWidget(self.right_scroll)

        main_splitter.addWidget(left_container)
        main_splitter.addWidget(right_container)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 1)

        layout.addWidget(main_splitter)

        self._setup_connections()

    def _setup_connections(self):
        """Set up signal/slot connections."""
        self.btn_open_left.clicked.connect(self._open_left_image)
        self.btn_open_right.clicked.connect(self._open_right_image)
        self.btn_overlay.toggled.connect(self._toggle_overlay)
        self.btn_diff.toggled.connect(self._toggle_diff)
        self.btn_reset.clicked.connect(self._reset_view)
        self.slider_zoom.valueChanged.connect(self._on_zoom_changed)
        self.slider_threshold.valueChanged.connect(self._on_threshold_changed)

    def _open_left_image(self):
        """Open an image file for the left pane."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Left Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp);;All Files (*)"
        )
        if file_path:
            self.set_left_image(file_path)

    def _open_right_image(self):
        """Open an image file for the right pane."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Right Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp);;All Files (*)"
        )
        if file_path:
            self.set_right_image(file_path)

    def _toggle_overlay(self, checked: bool):
        """Toggle overlay mode."""
        self._overlay_mode = checked
        if checked:
            self._update_overlay()
        else:
            self.left_image_label.set_show_diff(False)
            self.right_image_label.set_show_diff(False)

    def _toggle_diff(self, checked: bool):
        """Toggle diff highlighting."""
        if checked:
            self._compute_diff()
            self.left_image_label.set_show_diff(True)
            self.right_image_label.set_show_diff(True)
        else:
            self.left_image_label.set_show_diff(False)
            self.right_image_label.set_show_diff(False)

    def _reset_view(self):
        """Reset zoom and pan for both images."""
        self.left_image_label.reset_view()
        self.right_image_label.reset_view()
        self.slider_zoom.setValue(100)

    def _on_zoom_changed(self, value: int):
        """Handle zoom slider change."""
        scale = value / 100.0
        self.left_image_label.set_scale(scale)
        self.right_image_label.set_scale(scale)

    def _on_threshold_changed(self, value: int):
        """Handle diff threshold change."""
        self._diff_threshold = value
        if self.btn_diff.isChecked():
            self._compute_diff()

    def set_left_image(self, file_path: str):
        """Set the left image to display."""
        self._left_file_path = file_path
        try:
            self._left_image = QImage(file_path)
            if self._left_image.isNull():
                raise ValueError("Failed to load image")
            self.left_image_label.set_image(self._left_image)
            self._update_overlay()
            self.file_loaded.emit(file_path, self._right_file_path or "")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image:\n{e}")

    def set_right_image(self, file_path: str):
        """Set the right image to display."""
        self._right_file_path = file_path
        try:
            self._right_image = QImage(file_path)
            if self._right_image.isNull():
                raise ValueError("Failed to load image")
            self.right_image_label.set_image(self._right_image)
            self._update_overlay()
            self.file_loaded.emit(self._left_file_path or "", file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image:\n{e}")

    def compare_images(self, left_path: str, right_path: str):
        """Compare two image files."""
        self._left_file_path = left_path
        self._right_file_path = right_path

        try:
            self._left_image = QImage(left_path)
            if self._left_image.isNull():
                raise ValueError("Failed to load left image")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load left image:\n{e}")
            return

        try:
            self._right_image = QImage(right_path)
            if self._right_image.isNull():
                raise ValueError("Failed to load right image")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load right image:\n{e}")
            return

        self.left_image_label.set_image(self._left_image)
        self.right_image_label.set_image(self._right_image)
        self._update_overlay()
        self.file_loaded.emit(left_path, right_path)

    def _update_overlay(self):
        """Update overlay mode if enabled."""
        if self._overlay_mode and self._left_image and self._right_image:
            self._compute_diff()

    def _compute_diff(self):
        """Compute pixel-level differences between images."""
        if not self._left_image or not self._right_image:
            return

        left = self._left_image.convertToFormat(QImage.Format_ARGB32)
        right = self._right_image.convertToFormat(QImage.Format_ARGB32)

        width = min(left.width(), right.width())
        height = min(left.height(), right.height())

        diff_mask = QImage(width, height, QImage.Format_ARGB32)
        diff_mask.fill(QColor(0, 0, 0, 0))

        diff_count = 0
        threshold = self._diff_threshold

        for y in range(height):
            for x in range(width):
                left_pixel = left.pixel(x, y)
                right_pixel = right.pixel(x, y)

                left_r = (left_pixel >> 16) & 0xFF
                left_g = (left_pixel >> 8) & 0xFF
                left_b = left_pixel & 0xFF

                right_r = (right_pixel >> 16) & 0xFF
                right_g = (right_pixel >> 8) & 0xFF
                right_b = right_pixel & 0xFF

                diff_r = abs(left_r - right_r)
                diff_g = abs(left_g - right_g)
                diff_b = abs(left_b - right_b)

                if diff_r > threshold or diff_g > threshold or diff_b > threshold:
                    diff_mask.setPixel(x, y, QColor(255, 0, 0, 200).rgba())
                    diff_count += 1

        self.left_image_label.set_diff_mask(diff_mask)
        self.right_image_label.set_diff_mask(diff_mask)

        if diff_count > 0:
            diff_percentage = (diff_count / (width * height)) * 100
            self.parent().statusBar().showMessage(
                f"Found {diff_count} differing pixels ({diff_percentage:.2f}%)"
            )
        else:
            self.parent().statusBar().showMessage("Images are identical")

    def clear(self):
        """Clear both panes."""
        self._left_file_path = None
        self._right_file_path = None
        self._left_image = None
        self._right_image = None
        self.left_image_label.set_image(None)
        self.right_image_label.set_image(None)
        self.left_image_label.set_diff_mask(None)
        self.right_image_label.set_diff_mask(None)
