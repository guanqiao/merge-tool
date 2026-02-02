"""
Main application window for the Merge & Diff Tool.

Uses PySide6 for the GUI framework (LGPL licensed).
"""

import logging
logger = logging.getLogger("MergeDiffTool.MainWindow")

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QMenuBar, QMenu, QToolBar,
    QStatusBar, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from src.gui.diff_view import DiffView
from src.gui.file_tree import FileTreeView


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing MainWindow...")
        try:
            self.setWindowTitle("Merge & Diff Tool")
            self.setMinimumSize(QSize(800, 600))
            self._current_diff_result = None
            logger.info("MainWindow properties set")
            
            self._setup_ui()
            logger.info("UI setup completed")
            
            self._setup_menus()
            logger.info("Menus setup completed")
            
            self._setup_toolbar()
            logger.info("Toolbar setup completed")
            
            self._setup_connections()
            logger.info("Connections setup completed")
            
            logger.info("MainWindow initialization complete")
        except Exception as e:
            logger.error(f"Error initializing MainWindow: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for resizable panes
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: File tree (directory comparison)
        self.file_tree = FileTreeView()
        splitter.addWidget(self.file_tree)
        
        # Right side: Diff view
        self.diff_view = DiffView()
        splitter.addWidget(self.diff_view)
        
        # Set initial sizes (30% tree, 70% diff)
        splitter.setSizes([240, 560])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _setup_menus(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_left = file_menu.addAction("Open &Left...")
        open_left.setShortcut("Ctrl+1")
        
        open_right = file_menu.addAction("Open &Right...")
        open_right.setShortcut("Ctrl+2")
        
        file_menu.addSeparator()
        
        save_merged = file_menu.addAction("Save &Merged...")
        save_merged.setShortcut("Ctrl+S")
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        copy_left = edit_menu.addAction("Copy to Left")
        copy_left.setShortcut("Ctrl+L")
        
        copy_right = edit_menu.addAction("Copy to Right")
        copy_right.setShortcut("Ctrl+R")
        
        edit_menu.addSeparator()
        
        next_diff = edit_menu.addAction("Next Difference")
        next_diff.setShortcut("F8")
        
        prev_diff = edit_menu.addAction("Previous Difference")
        prev_diff.setShortcut("F7")
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = help_menu.addAction("&About")
        
        # Store actions for connections
        self._actions = {
            "open_left": open_left,
            "open_right": open_right,
            "save_merged": save_merged,
            "exit": exit_action,
            "copy_left": copy_left,
            "copy_right": copy_right,
            "next_diff": next_diff,
            "prev_diff": prev_diff,
            "about": about_action
        }
    
    def _setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        toolbar.addAction("Open Left")
        toolbar.addAction("Open Right")
        toolbar.addSeparator()
        toolbar.addAction("Copy to Left")
        toolbar.addAction("Copy to Right")
        toolbar.addSeparator()
        toolbar.addAction("Next")
        toolbar.addAction("Prev")
    
    def _setup_connections(self):
        """Set up signal/slot connections."""
        self._actions["open_left"].triggered.connect(self._open_left_file)
        self._actions["open_right"].triggered.connect(self._open_right_file)
        self._actions["save_merged"].triggered.connect(self._save_merged)
        self._actions["exit"].triggered.connect(self.close)
        self._actions["copy_left"].triggered.connect(self._copy_to_left)
        self._actions["copy_right"].triggered.connect(self._copy_to_right)
        self._actions["next_diff"].triggered.connect(self._next_difference)
        self._actions["prev_diff"].triggered.connect(self._prev_difference)
        self._actions["about"].triggered.connect(self._show_about)
        
        # Connect file tree selection to diff view
        self.file_tree.file_selected.connect(self._on_file_selected)
    
    def _open_left_file(self):
        """Open a file for the left pane."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Left File", "", "All Files (*);;Text Files (*.txt);;Python Files (*.py)"
        )
        if file_path:
            self.diff_view.set_left_file(file_path)
            self.status_bar.showMessage(f"Opened: {file_path}")
    
    def _open_right_file(self):
        """Open a file for the right pane."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Right File", "", "All Files (*);;Text Files (*.txt);;Python Files (*.py)"
        )
        if file_path:
            self.diff_view.set_right_file(file_path)
            self.status_bar.showMessage(f"Opened: {file_path}")
    
    def _save_merged(self):
        """Save the merged result."""
        self.diff_view.save_merged()
    
    def _copy_to_left(self):
        """Copy selected changes to left pane."""
        self.diff_view.copy_to_left()
    
    def _copy_to_right(self):
        """Copy selected changes to right pane."""
        self.diff_view.copy_to_right()
    
    def _next_difference(self):
        """Navigate to next difference."""
        self.diff_view.next_difference()
    
    def _prev_difference(self):
        """Navigate to previous difference."""
        self.diff_view.prev_difference()
    
    def _on_file_selected(self, left_path: str, right_path: str):
        """Handle file selection from the file tree."""
        if left_path and right_path:
            self.diff_view.compare_files(left_path, right_path)
            self.status_bar.showMessage(f"Comparing: {left_path} vs {right_path}")
    
    def _show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About Merge & Diff Tool",
            "Merge & Diff Tool\n\n"
            "A WinMerge-like GUI tool for comparing and merging files.\n\n"
            "Built with Python and PySide6."
        )
