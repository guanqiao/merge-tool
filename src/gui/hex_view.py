"""
Hex view widget for displaying binary files.

Provides a hex editor functionality with ASCII representation.
"""

import logging
logger = logging.getLogger("MergeDiffTool.HexView")

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPlainTextEdit,
    QScrollBar, QLabel, QFrame, QPushButton, QFileDialog,
    QMessageBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QTextCursor, QFont, QColor, QPainter, QKeyEvent
from typing import Optional, List, Tuple
import os


class HexEditor(QPlainTextEdit):
    """Custom text editor for hex editing."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Courier New", 10))
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        self._data = bytearray()
        self._bytes_per_line = 16

    def set_data(self, data: bytes):
        """Set the binary data to display."""
        self._data = bytearray(data)
        self._update_display()

    def get_data(self) -> bytes:
        """Get the current binary data."""
        return bytes(self._data)

    def _update_display(self):
        """Update the hex display."""
        lines = []
        for i in range(0, len(self._data), self._bytes_per_line):
            chunk = self._data[i:i + self._bytes_per_line]
            
            offset = f"{i:08x}"
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            hex_part = hex_part.ljust(self._bytes_per_line * 3 - 1)
            
            ascii_part = ""
            for b in chunk:
                if 32 <= b <= 126:
                    ascii_part += chr(b)
                else:
                    ascii_part += "."
            
            line = f"{offset}  {hex_part}  |{ascii_part}|"
            lines.append(line)
        
        self.setPlainText("\n".join(lines))

    def set_bytes_per_line(self, count: int):
        """Set the number of bytes to display per line."""
        self._bytes_per_line = max(8, min(32, count))
        self._update_display()

    def get_bytes_per_line(self) -> int:
        """Get the current bytes per line setting."""
        return self._bytes_per_line


class HexView(QWidget):
    """Widget for displaying and comparing binary files in hex format."""

    file_loaded = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("HexView.__init__ called")
        self._left_file_path = None
        self._right_file_path = None
        self._left_data = bytearray()
        self._right_data = bytearray()
        self._diff_enabled = True

        logger.debug("Calling _setup_ui...")
        self._setup_ui()
        logger.debug("HexView initialization complete")

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)

        self.btn_open_left = QPushButton("Open Left...")
        self.btn_open_right = QPushButton("Open Right...")
        self.btn_diff = QPushButton("Compare")
        self.btn_diff.setCheckable(True)
        self.btn_diff.setChecked(True)
        self.btn_save_left = QPushButton("Save Left...")
        self.btn_save_right = QPushButton("Save Right...")

        toolbar_layout.addWidget(self.btn_open_left)
        toolbar_layout.addWidget(self.btn_open_right)
        toolbar_layout.addWidget(self.btn_diff)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_save_left)
        toolbar_layout.addWidget(self.btn_save_right)

        layout.addWidget(toolbar)

        main_splitter = QSplitter(Qt.Horizontal)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_label = QLabel("Left File")
        left_label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.left_hex = HexEditor()
        left_layout.addWidget(left_label)
        left_layout.addWidget(self.left_hex)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_label = QLabel("Right File")
        right_label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.right_hex = HexEditor()
        right_layout.addWidget(right_label)
        right_layout.addWidget(self.right_hex)

        main_splitter.addWidget(left_container)
        main_splitter.addWidget(right_container)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 1)

        layout.addWidget(main_splitter)

        self._setup_connections()

    def _setup_connections(self):
        """Set up signal/slot connections."""
        self.btn_open_left.clicked.connect(self._open_left_file)
        self.btn_open_right.clicked.connect(self._open_right_file)
        self.btn_diff.toggled.connect(self._toggle_diff)
        self.btn_save_left.clicked.connect(self._save_left_file)
        self.btn_save_right.clicked.connect(self._save_right_file)

    def _open_left_file(self):
        """Open a binary file for the left pane."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Left Binary File", "", "All Files (*)"
        )
        if file_path:
            self.set_left_file(file_path)

    def _open_right_file(self):
        """Open a binary file for the right pane."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Right Binary File", "", "All Files (*)"
        )
        if file_path:
            self.set_right_file(file_path)

    def _save_left_file(self):
        """Save the left binary data to a file."""
        if not self._left_file_path:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Left Binary File", "", "All Files (*)"
            )
            if not file_path:
                return
            self._left_file_path = file_path
        else:
            file_path = self._left_file_path

        try:
            with open(file_path, "wb") as f:
                f.write(self.left_hex.get_data())
            QMessageBox.information(self, "Success", f"File saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def _save_right_file(self):
        """Save the right binary data to a file."""
        if not self._right_file_path:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Right Binary File", "", "All Files (*)"
            )
            if not file_path:
                return
            self._right_file_path = file_path
        else:
            file_path = self._right_file_path

        try:
            with open(file_path, "wb") as f:
                f.write(self.right_hex.get_data())
            QMessageBox.information(self, "Success", f"File saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def _toggle_diff(self, checked: bool):
        """Toggle diff highlighting."""
        self._diff_enabled = checked
        self._update_diff()

    def set_left_file(self, file_path: str):
        """Set the left binary file to display."""
        self._left_file_path = file_path
        try:
            with open(file_path, "rb") as f:
                self._left_data = bytearray(f.read())
            self.left_hex.set_data(self._left_data)
            self._update_diff()
            self.file_loaded.emit(file_path, self._right_file_path or "")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read file:\n{e}")

    def set_right_file(self, file_path: str):
        """Set the right binary file to display."""
        self._right_file_path = file_path
        try:
            with open(file_path, "rb") as f:
                self._right_data = bytearray(f.read())
            self.right_hex.set_data(self._right_data)
            self._update_diff()
            self.file_loaded.emit(self._left_file_path or "", file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read file:\n{e}")

    def compare_files(self, left_path: str, right_path: str):
        """Compare two binary files."""
        self._left_file_path = left_path
        self._right_file_path = right_path

        try:
            with open(left_path, "rb") as f:
                self._left_data = bytearray(f.read())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read left file:\n{e}")
            return

        try:
            with open(right_path, "rb") as f:
                self._right_data = bytearray(f.read())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read right file:\n{e}")
            return

        self.left_hex.set_data(self._left_data)
        self.right_hex.set_data(self._right_data)
        self._update_diff()
        self.file_loaded.emit(left_path, right_path)

    def _update_diff(self):
        """Update the diff highlighting between left and right panes."""
        if not self._diff_enabled:
            return

        if not self._left_data or not self._right_data:
            return

        max_len = max(len(self._left_data), len(self._right_data))
        diff_positions = []

        for i in range(max_len):
            left_byte = self._left_data[i] if i < len(self._left_data) else None
            right_byte = self._right_data[i] if i < len(self._right_data) else None

            if left_byte != right_byte:
                diff_positions.append(i)

        if diff_positions:
            self._highlight_diffs(diff_positions)

    def _highlight_diffs(self, positions: List[int]):
        """Highlight differing bytes in both hex editors."""
        bytes_per_line = self.left_hex.get_bytes_per_line()

        for pos in positions:
            line_num = pos // bytes_per_line
            byte_in_line = pos % bytes_per_line

            left_text = self.left_hex.toPlainText()
            right_text = self.right_hex.toPlainText()

            lines = left_text.split('\n')
            if line_num < len(lines):
                line = lines[line_num]
                offset = 10
                hex_start = offset + byte_in_line * 3
                if hex_start < len(line):
                    self._highlight_line(self.left_hex, line_num, hex_start, 2)

            lines = right_text.split('\n')
            if line_num < len(lines):
                line = lines[line_num]
                offset = 10
                hex_start = offset + byte_in_line * 3
                if hex_start < len(line):
                    self._highlight_line(self.right_hex, line_num, hex_start, 2)

    def _highlight_line(self, editor: HexEditor, line_num: int, start_pos: int, length: int):
        """Highlight a portion of a line in the editor."""
        cursor = editor.textCursor()
        block = editor.document().findBlockByNumber(line_num)
        if block.isValid():
            cursor.setPosition(block.position() + start_pos)
            cursor.setPosition(block.position() + start_pos + length, QTextCursor.KeepAnchor)
            fmt = cursor.charFormat()
            fmt.setBackground(QColor("#ff6b6b"))
            cursor.setCharFormat(fmt)
            editor.setTextCursor(cursor)

    def clear(self):
        """Clear both panes."""
        self._left_file_path = None
        self._right_file_path = None
        self._left_data = bytearray()
        self._right_data = bytearray()
        self.left_hex.set_data(b"")
        self.right_hex.set_data(b"")
