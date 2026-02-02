"""
File tree view for directory comparison.

Displays two directories side-by-side for comparison.
"""

import os
import logging
logger = logging.getLogger("MergeDiffTool.FileTreeView")

from typing import Optional, Tuple
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QSplitter, QTreeView, 
    QFrame, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QFileSystemModel, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QDir
from PySide6.QtGui import QFont, QIcon


class DirectoryTree(QWidget):
    """Widget for displaying a single directory tree."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._root_path = ""
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with path
        header_layout = QHBoxLayout()
        
        self.path_label = QLabel("No folder selected")
        self.path_label.setStyleSheet("font-weight: bold; padding: 2px;")
        header_layout.addWidget(self.path_label)
        
        # Browse button
        browse_btn = QPushButton("...")
        browse_btn.setMaximumWidth(30)
        browse_btn.clicked.connect(self._browse_folder)
        header_layout.addWidget(browse_btn)
        
        layout.addLayout(header_layout)
        
        # Tree view
        self.tree_view = QTreeView()
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.setHeaderHidden(False)
        
        # File system model
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        self.model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        
        # Set column widths
        self.tree_view.setModel(self.model)
        self.tree_view.setColumnWidth(0, 200)  # Name
        self.tree_view.setColumnWidth(1, 80)   # Size
        self.tree_view.setColumnWidth(2, 150)  # Type
        self.tree_view.setColumnWidth(3, 150)  # Date
        
        # Hide some columns for cleaner view
        self.tree_view.hideColumn(1)  # Hide size
        self.tree_view.hideColumn(2)  # Hide type
        self.tree_view.hideColumn(3)  # Hide date
        
        layout.addWidget(self.tree_view)
    
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
            root_index = self.model.setRootPath(path)
            self.tree_view.setRootIndex(root_index)
        else:
            self.tree_view.setRootIndex(self.model.index(""))
    
    def get_selected_path(self) -> Optional[str]:
        """Get the currently selected file/folder path."""
        index = self.tree_view.currentIndex()
        if index.isValid():
            return self.model.filePath(index)
        return None
    
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


class FileTreeView(QWidget):
    """Widget for displaying two directory trees side-by-side."""
    
    # Signal emitted when a file is selected for comparison
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
        
        # Create splitter for left/right trees
        splitter = QSplitter(Qt.Horizontal)
        
        # Left tree
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
        
        # Right tree
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
        # Try to find corresponding left file
        left_path = self._find_corresponding_file(right_path)
        self.file_selected.emit(left_path, right_path)
    
    def _find_corresponding_file(self, right_path: str) -> str:
        """Find corresponding file in left directory."""
        if not self._left_path:
            return right_path
        
        # Get relative path from right root
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
