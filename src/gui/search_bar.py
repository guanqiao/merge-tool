"""
Search and replace bar widget for diff view.

Provides find and replace functionality with support for regex,
case sensitivity, and whole word matching.
"""

import re
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton,
    QCheckBox, QLabel, QFrame, QToolButton
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QIcon, QKeySequence


class SearchBar(QWidget):
    """Search and replace bar widget."""

    search_requested = Signal(str, bool, bool, bool)
    replace_requested = Signal(str, str)
    replace_all_requested = Signal(str, str)
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.find_label = QLabel("Find:")
        layout.addWidget(self.find_label)

        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("Search text...")
        self.find_edit.setMinimumWidth(200)
        layout.addWidget(self.find_edit)

        self.replace_label = QLabel("Replace:")
        layout.addWidget(self.replace_label)

        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("Replacement text...")
        self.replace_edit.setMinimumWidth(200)
        layout.addWidget(self.replace_edit)

        layout.addSpacing(10)

        self.case_sensitive = QCheckBox("Case")
        self.case_sensitive.setToolTip("Match case")
        layout.addWidget(self.case_sensitive)

        self.whole_word = QCheckBox("Whole Word")
        self.whole_word.setToolTip("Match whole word only")
        layout.addWidget(self.whole_word)

        self.regex = QCheckBox("Regex")
        self.regex.setToolTip("Use regular expressions")
        layout.addWidget(self.regex)

        layout.addSpacing(10)

        self.find_next_btn = QPushButton("Find Next")
        self.find_next_btn.setToolTip("Find next occurrence (F3)")
        layout.addWidget(self.find_next_btn)

        self.find_prev_btn = QPushButton("Find Prev")
        self.find_prev_btn.setToolTip("Find previous occurrence (Shift+F3)")
        layout.addWidget(self.find_prev_btn)

        self.replace_btn = QPushButton("Replace")
        self.replace_btn.setToolTip("Replace current occurrence")
        layout.addWidget(self.replace_btn)

        self.replace_all_btn = QPushButton("Replace All")
        self.replace_all_btn.setToolTip("Replace all occurrences")
        layout.addWidget(self.replace_all_btn)

        layout.addStretch()

        self.close_btn = QToolButton()
        self.close_btn.setText("×")
        self.close_btn.setToolTip("Close search bar (Esc)")
        self.close_btn.setMaximumSize(30, 30)
        layout.addWidget(self.close_btn)

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border-bottom: 1px solid #cccccc;
            }
            QLineEdit {
                padding: 3px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #1890ff;
            }
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #e6f7ff;
                border-color: #1890ff;
            }
            QPushButton:pressed {
                background-color: #bae7ff;
            }
            QToolButton {
                border: none;
                background-color: transparent;
                font-size: 16px;
                font-weight: bold;
            }
            QToolButton:hover {
                color: #ff0000;
            }
        """)

    def _setup_connections(self):
        """Set up signal/slot connections."""
        self.find_next_btn.clicked.connect(self._on_find_next)
        self.find_prev_btn.clicked.connect(self._on_find_prev)
        self.replace_btn.clicked.connect(self._on_replace)
        self.replace_all_btn.clicked.connect(self._on_replace_all)
        self.close_btn.clicked.connect(self.close_requested.emit)
        self.find_edit.returnPressed.connect(self._on_find_next)
        self.replace_edit.returnPressed.connect(self._on_replace)

    def _on_find_next(self):
        """Handle find next button click."""
        search_text = self.find_edit.text()
        if search_text:
            self.search_requested.emit(
                search_text,
                self.case_sensitive.isChecked(),
                self.whole_word.isChecked(),
                self.regex.isChecked()
            )

    def _on_find_prev(self):
        """Handle find previous button click."""
        search_text = self.find_edit.text()
        if search_text:
            self.search_requested.emit(
                search_text,
                self.case_sensitive.isChecked(),
                self.whole_word.isChecked(),
                self.regex.isChecked()
            )

    def _on_replace(self):
        """Handle replace button click."""
        find_text = self.find_edit.text()
        replace_text = self.replace_edit.text()
        if find_text:
            self.replace_requested.emit(find_text, replace_text)

    def _on_replace_all(self):
        """Handle replace all button click."""
        find_text = self.find_edit.text()
        replace_text = self.replace_edit.text()
        if find_text:
            self.replace_all_requested.emit(find_text, replace_text)

    def get_search_text(self) -> str:
        """Get the current search text."""
        return self.find_edit.text()

    def get_replace_text(self) -> str:
        """Get the current replacement text."""
        return self.replace_edit.text()

    def is_case_sensitive(self) -> bool:
        """Check if case sensitive search is enabled."""
        return self.case_sensitive.isChecked()

    def is_whole_word(self) -> bool:
        """Check if whole word search is enabled."""
        return self.whole_word.isChecked()

    def is_regex(self) -> bool:
        """Check if regex search is enabled."""
        return self.regex.isChecked()

    def set_search_text(self, text: str):
        """Set the search text."""
        self.find_edit.setText(text)

    def set_replace_text(self, text: str):
        """Set the replacement text."""
        self.replace_edit.setText(text)

    def focus_find(self):
        """Focus on the find edit box."""
        self.find_edit.setFocus()
        self.find_edit.selectAll()

    def focus_replace(self):
        """Focus on the replace edit box."""
        self.replace_edit.setFocus()
        self.replace_edit.selectAll()


class SearchHelper:
    """Helper class for search operations."""

    @staticmethod
    def build_pattern(search_text: str, case_sensitive: bool, 
                     whole_word: bool, use_regex: bool) -> re.Pattern:
        """Build a regex pattern for searching."""
        if not use_regex:
            search_text = re.escape(search_text)
        
        if whole_word:
            search_text = r'\b' + search_text + r'\b'
        
        flags = 0 if case_sensitive else re.IGNORECASE
        return re.compile(search_text, flags)

    @staticmethod
    def find_in_text(text: str, pattern: re.Pattern, 
                    start_pos: int = 0, forward: bool = True) -> int:
        """Find pattern in text starting from position."""
        if forward:
            match = pattern.search(text, start_pos)
            return match.start() if match else -1
        else:
            matches = list(pattern.finditer(text, 0, start_pos))
            return matches[-1].start() if matches else -1

    @staticmethod
    def replace_in_text(text: str, pattern: re.Pattern, 
                        replacement: str) -> str:
        """Replace all occurrences of pattern in text."""
        return pattern.sub(replacement, text)

    @staticmethod
    def count_matches(text: str, pattern: re.Pattern) -> int:
        """Count the number of matches in text."""
        return len(list(pattern.finditer(text)))