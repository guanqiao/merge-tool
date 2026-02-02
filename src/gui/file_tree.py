"""
File tree view for directory comparison.

Displays two directories side-by-side for comparison.
Supports file filtering similar to WinMerge.
"""

import os
import logging
import fnmatch
logger = logging.getLogger("MergeDiffTool.FileTreeView")

from typing import Optional, Tuple, List
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QSplitter, QTreeView,
    QFrame, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QFileSystemModel, QHeaderView,
    QComboBox, QToolBar, QApplication
)
from PySide6.QtCore import Qt, Signal, QDir, QEvent, QSortFilterProxyModel
from PySide6.QtGui import QFont, QIcon
from src.utils.config import load_filters, FileFilter


class FilteredFileSystemModel(QFileSystemModel):
    """File system model with filtering support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._include_patterns: List[str] = []
        self._exclude_patterns: List[str] = []

    def set_include_patterns(self, patterns: List[str]):
        """Set include patterns for filtering."""
        self._include_patterns = patterns

    def set_exclude_patterns(self, patterns: List[str]):
        """Set exclude patterns for filtering."""
        self._exclude_patterns = patterns

    def _matches_pattern(self, filename: str, patterns: List[str]) -> bool:
        """Check if filename matches any of the patterns."""
        filename_lower = filename.lower()
        for pattern in patterns:
            pattern_lower = pattern.lower()
            if pattern_lower.endswith("*"):
                prefix = pattern_lower[:-1]
                if filename_lower.startswith(prefix):
                    return True
            elif pattern_lower.startswith("*"):
                suffix = pattern_lower[1:]
                if filename_lower.endswith(suffix):
                    return True
            elif fnmatch.fnmatch(filename_lower, pattern_lower):
                return True
        return False

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        """Filter rows based on include/exclude patterns."""
        index = self.index(source_row, 0, source_parent)
        filename = self.fileName(index)
        filepath = self.filePath(index)

        if os.path.isdir(filepath):
            return True

        if self._exclude_patterns and self._matches_pattern(filename, self._exclude_patterns):
            return False

        if self._include_patterns and not self._matches_pattern(filename, self._include_patterns):
            return False

        return True


class DirectoryTree(QWidget):
    """Widget for displaying a single directory tree."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root_path = self
        self._setup_ui()
        self._setup_drag_drop()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))

        self.path_label = QLabel("No folder selected")
        self.path_label.setStyleSheet("font-weight: bold; padding: 2px;")

        browse_btn = QPushButton("...")
        browse_btn.setMaximumWidth(25)
        browse_btn.clicked.connect(self._browse_folder)

        toolbar.addWidget(self.path_label)
        toolbar.addWidget(browse_btn)

        toolbar.addSeparator()

        filter_label = QLabel("Filter:")
        toolbar.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.setMinimumWidth(120)
        self.filter_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._load_filters()
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.filter_combo)

        layout.addWidget(toolbar)

        self.tree_view = QTreeView()
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.setHeaderHidden(False)

        self.model = FilteredFileSystemModel()
        self.model.setRootPath("")
        self.model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterRole(Qt.ItemDataRole.FilePathRole)

        self.tree_view.setModel(self.proxy_model)
        self.tree_view.setColumnWidth(0, 200)
        self.tree_view.setColumnWidth(1, 80)
        self.tree_view.setColumnWidth(2, 150)
        self.tree_view.setColumnWidth(3, 150)

        self.tree_view.hideColumn(1)
        self.tree_view.hideColumn(2)
        self.tree_view.hideColumn(3)

        layout.addWidget(self.tree_view)

    def _load_filters(self):
        """Load available filters into combo box."""
        filters = load_filters()
        self._filters = filters

        self.filter_combo.clear()
        self.filter_combo.addItem("All Files", "")
        self.filter_combo.addItem("Custom Filter...", "custom")

        for f in filters:
            self.filter_combo.addItem(f.name, f.name)

        self.filter_combo.setCurrentIndex(0)

    def _on_filter_changed(self, index):
        """Handle filter selection change."""
        filter_name = self.filter_combo.currentData()

        if filter_name == "custom":
            self._show_custom_filter_dialog()
            return

        if not filter_name:
            self.model.set_include_patterns([])
            self.model.set_exclude_patterns([])
        else:
            for f in self._filters:
                if f.name == filter_name:
                    self.model.set_include_patterns(f.include_patterns)
                    self.model.set_exclude_patterns(f.exclude_patterns)
                    break

        self.tree_view.expandAll()

    def _show_custom_filter_dialog(self):
        """Show dialog for custom filter patterns."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Custom Filter")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Include patterns (comma-separated, e.g., *.py, *.txt):"))
        self.include_edit = QLineEdit()
        self.include_edit.setPlaceholderText("*.py, *.txt, src/**")
        layout.addWidget(self.include_edit)

        layout.addWidget(QLabel("Exclude patterns (comma-separated, e.g., *.pyc, __pycache__):"))
        self.exclude_edit = QLineEdit()
        self.exclude_edit.setPlaceholderText("*.pyc, __pycache__")
        layout.addWidget(self.exclude_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            include_text = self.include_edit.text().strip()
            exclude_text = self.exclude_edit.text().strip()

            include_patterns = [p.strip() for p in include_text.split(",") if p.strip()]
            exclude_patterns = [p.strip() for p in exclude_text.split(",") if p.strip()]

            self.model.set_include_patterns(include_patterns)
            self.model.set_exclude_patterns(exclude_patterns)

            current_text = self.filter_combo.currentText()
            self.filter_combo.setItemText(self.filter_combo.currentIndex(), f"Custom: {current_text}")
        else:
            self.filter_combo.setCurrentIndex(0)

    def _browse_folder(self):
        """Open a folder browser dialog."""
        folder = self.model.filePath(self.tree_view.rootIndex())
        if not folder:
            folder = ""

        new_folder = QFileDialog.getExistingDirectory(
            self, "Select Folder", folder
        )

        if new_folder:
            self.set_root_path(new_folder)

    def set_root_path(self, path: str):
        """Set the root path to display."""
        self._root_path = path
        self.path_label.setText(path if path else "No folder selected")

        if path and os.path.exists(path):
            source_index = self.model.setRootPath(path)
            proxy_index = self.proxy_model.mapFromSource(source_index)
            self.tree_view.setRootIndex(proxy_index)
        else:
            self.tree_view.setRootIndex(self.proxy_model.index(""))

    def get_selected_path(self) -> Optional[str]:
        """Get the currently selected file/folder path."""
        index = self.tree_view.currentIndex()
        if index.isValid():
            source_index = self.proxy_model.mapToSource(index)
            return self.model.filePath(source_index)
        return None

    def _setup_drag_drop(self):
        """Set up drag and drop support for folders."""
        self.setAcceptDrops(True)
        self.tree_view.setAcceptDrops(True)
        self.tree_view.installEventFilter(self)

    def set_compare_mode(self, is_left: bool = True):
        """Set visual mode (left or right side)."""
        color = "#e6f7ff" if is_left else "#f6ffed"
        self.tree_view.setStyleSheet(f"""
            QTreeView {{
                background-color: {color};
            }}
            QTreeView::item:selected {{
                background-color: #1890ff;
                color: white;
            }}
        """)

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop event on the directory tree."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                folder_path = urls[0].toLocalFile()
                if os.path.isdir(folder_path):
                    self.set_root_path(folder_path)

    def eventFilter(self, obj, event):
        """Handle drag and drop events for the tree view."""
        if event.type() == QEvent.DragEnter and event.mimeData().hasUrls():
            event.acceptProposedAction()
            return True
        elif event.type() == QEvent.Drop and event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                folder_path = urls[0].toLocalFile()
                if os.path.isdir(folder_path):
                    self.set_root_path(folder_path)
            return True
        return False


class FileTreeView(QWidget):
    """Widget for displaying two directory trees side-by-side."""

    file_selected = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("FileTreeView.__init__ called")
        self._left_path = ""
        self._right_path = ""

        logger.debug("Calling _setup_ui...")
        self._setup_ui()
        logger.debug("Calling _setup_connections...")
        self._setup_connections()
        logger.debug("FileTreeView initialization complete")

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)

        left_frame = QFrame()
        left_frame.setFrameStyle(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(5, 5, 5, 5)

        left_label = QLabel("<b>Left (Original)</b>")
        left_layout.addWidget(left_label)

        self.left_tree = DirectoryTree()
        self.left_tree.set_compare_mode(is_left=True)
        left_layout.addWidget(self.left_tree)

        splitter.addWidget(left_frame)

        right_frame = QFrame()
        right_frame.setFrameStyle(QFrame.StyledPanel)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(5, 5, 5, 5)

        right_label = QLabel("<b>Right (Modified)</b>")
        right_layout.addWidget(right_label)

        self.right_tree = DirectoryTree()
        self.right_tree.set_compare_mode(is_left=False)
        right_layout.addWidget(self.right_tree)

        splitter.addWidget(right_frame)

        layout.addWidget(splitter)

    def _setup_connections(self):
        """Set up signal/slot connections."""
        self.left_tree.tree_view.doubleClicked.connect(
            self._on_left_double_click
        )
        self.right_tree.tree_view.doubleClicked.connect(
            self._on_right_double_click
        )

    def _on_left_double_click(self, index):
        """Handle double-click on left tree."""
        path = self.left_tree.get_selected_path()
        if path and os.path.isfile(path):
            self._emit_file_pair(path)

    def _on_right_double_click(self, index):
        """Handle double-click on right tree."""
        path = self.right_tree.get_selected_path()
        if path and os.path.isfile(path):
            self._emit_file_pair(path)

    def _emit_file_pair(self, right_path: str):
        """Emit file pair signal for comparison."""
        left_path = self._find_corresponding_file(right_path)
        self.file_selected.emit(left_path, right_path)

    def _find_corresponding_file(self, right_path: str) -> str:
        """Find corresponding file in left directory."""
        if not self._left_path:
            return right_path

        if self._right_path and right_path.startswith(self._right_path):
            rel_path = right_path[len(self._right_path):].lstrip(os.sep)
            left_path = os.path.join(self._left_path, rel_path)
            if os.path.exists(left_path):
                return left_path

        return right_path

    def set_left_path(self, path: str):
        """Set the left directory path."""
        self._left_path = path
        self.left_tree.set_root_path(path)

    def set_right_path(self, path: str):
        """Set the right directory path."""
        self._right_path = path
        self.right_tree.set_root_path(path)

    def compare_directories(self, left_path: str, right_path: str):
        """Compare two directories."""
        self._left_path = left_path
        self._right_path = right_path
        self.left_tree.set_root_path(left_path)
        self.right_tree.set_root_path(right_path)

    def set_filter(self, filter_name: str):
        """Set the active filter for both trees."""
        left_index = self.left_tree.filter_combo.findData(filter_name)
        right_index = self.right_tree.filter_combo.findData(filter_name)

        if left_index >= 0:
            self.left_tree.filter_combo.setCurrentIndex(left_index)
        if right_index >= 0:
            self.right_tree.filter_combo.setCurrentIndex(right_index)
