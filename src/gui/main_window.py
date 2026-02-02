"""
Main application window for the Merge & Diff Tool.

Uses PySide6 for the GUI framework (LGPL licensed).
"""

import logging
import os
logger = logging.getLogger("MergeDiffTool.MainWindow")

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QMenuBar, QMenu, QToolBar,
    QStatusBar, QFileDialog, QMessageBox, QTabWidget,
    QWidgetAction, QLineEdit, QComboBox
)
from PySide6.QtCore import Qt, QSize, Signal
from src.gui.diff_view import DiffView
from src.gui.file_tree import FileTreeView
from src.gui.three_way_merge import ThreeWayMergeView
from src.utils.config import load_config, save_config, AppConfig, add_recent_file, add_recent_folder


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        logger.info("Initializing MainWindow...")

        self.config = load_config()
        self._three_way_merge_view = None
        self._recent_file_actions = []
        self._recent_folder_actions = []

        try:
            self.setWindowTitle("Merge & Diff Tool")
            self.setMinimumSize(QSize(800, 600))
            self._current_diff_result = None

            if hasattr(self.config, 'window_x') and hasattr(self.config, 'window_y'):
                self.move(self.config.window_x, self.config.window_y)
            self.resize(self.config.window_width, self.config.window_height)
            if self.config.window_maximized:
                self.setWindowState(Qt.WindowState.WindowMaximized)

            self._setup_ui()
            logger.info("UI setup completed")

            self._setup_menus()
            logger.info("Menus setup completed")

            self._setup_toolbar()
            logger.info("Toolbar setup completed")

            self._setup_connections()
            logger.info("Connections setup completed")

            self._update_recent_files_menu()
            self._update_recent_folders_menu()

            logger.info("MainWindow initialization complete")
        except Exception as e:
            logger.error(f"Error initializing MainWindow: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setDocumentMode(True)

        self.diff_view = DiffView()
        self.tab_widget.addTab(self.diff_view, "Diff View")

        main_layout.addWidget(self.tab_widget)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _setup_menus(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        open_left = file_menu.addAction("Open &Left...")
        open_left.setShortcut("Ctrl+1")

        open_right = file_menu.addAction("Open &Right...")
        open_right.setShortcut("Ctrl+2")

        compare_folders = file_menu.addAction("&Compare Folders...")
        compare_folders.setShortcut("Ctrl+3")

        file_menu.addSeparator()

        save_merged = file_menu.addAction("Save &Merged...")
        save_merged.setShortcut("Ctrl+S")

        file_menu.addSeparator()

        self.recent_files_menu = file_menu.addMenu("Recent &Files")
        self.recent_folders_menu = file_menu.addMenu("Recent F&olders")

        file_menu.addSeparator()

        open_three_way = file_menu.addAction("3-Way Merge...")
        open_three_way.setShortcut("Ctrl+M")

        file_menu.addSeparator()

        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")

        edit_menu = menubar.addMenu("&Edit")

        undo_action = edit_menu.addAction("&Undo")
        undo_action.setShortcut("Ctrl+Z")

        redo_action = edit_menu.addAction("&Redo")
        redo_action.setShortcut("Ctrl+Y")

        edit_menu.addSeparator()

        copy_left = edit_menu.addAction("Copy to Left")
        copy_left.setShortcut("Ctrl+L")

        copy_right = edit_menu.addAction("Copy to Right")
        copy_right.setShortcut("Ctrl+R")

        edit_menu.addSeparator()

        next_diff = edit_menu.addAction("Next Difference")
        next_diff.setShortcut("F8")

        prev_diff = edit_menu.addAction("Previous Difference")
        prev_diff.setShortcut("F7")

        view_menu = menubar.addMenu("&View")

        toggle_folders = view_menu.addAction("Show &Folder Comparison")
        toggle_folders.setCheckable(True)
        toggle_folders.setChecked(False)

        view_menu.addSeparator()

        self.action_inline_diff = view_menu.addAction("Inline Diff Mode")
        self.action_inline_diff.setCheckable(True)
        self.action_inline_diff.setShortcut("Ctrl+I")

        help_menu = menubar.addMenu("&Help")

        about_action = help_menu.addAction("&About")

        self._actions = {
            "open_left": open_left,
            "open_right": open_right,
            "compare_folders": compare_folders,
            "save_merged": save_merged,
            "exit": exit_action,
            "undo": undo_action,
            "redo": redo_action,
            "copy_left": copy_left,
            "copy_right": copy_right,
            "next_diff": next_diff,
            "prev_diff": prev_diff,
            "toggle_folders": toggle_folders,
            "about": about_action,
            "open_three_way": open_three_way,
            "inline_diff": self.action_inline_diff
        }

    def _setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        toolbar.addAction(self._actions["open_left"])
        toolbar.addAction(self._actions["open_right"])
        toolbar.addSeparator()
        toolbar.addAction(self._actions["undo"])
        toolbar.addAction(self._actions["redo"])
        toolbar.addSeparator()
        toolbar.addAction(self._actions["copy_left"])
        toolbar.addAction(self._actions["copy_right"])
        toolbar.addSeparator()
        toolbar.addAction(self._actions["next_diff"])
        toolbar.addAction(self._actions["prev_diff"])
        toolbar.addSeparator()
        toolbar.addAction(self._actions["inline_diff"])

    def _setup_connections(self):
        """Set up signal/slot connections."""
        self._actions["open_left"].triggered.connect(self._open_left_file)
        self._actions["open_right"].triggered.connect(self._open_right_file)
        self._actions["compare_folders"].triggered.connect(self._compare_folders)
        self._actions["save_merged"].triggered.connect(self._save_merged)
        self._actions["exit"].triggered.connect(self.close)
        self._actions["undo"].triggered.connect(self._undo)
        self._actions["redo"].triggered.connect(self._redo)
        self._actions["copy_left"].triggered.connect(self._copy_to_left)
        self._actions["copy_right"].triggered.connect(self._copy_to_right)
        self._actions["next_diff"].triggered.connect(self._next_difference)
        self._actions["prev_diff"].triggered.connect(self._prev_difference)
        self._actions["toggle_folders"].triggered.connect(self._toggle_folder_view)
        self._actions["about"].triggered.connect(self._show_about)
        self._actions["open_three_way"].triggered.connect(self._open_three_way_merge)
        self._actions["inline_diff"].triggered.connect(self._toggle_inline_diff)

        self.tab_widget.tabCloseRequested.connect(self._close_tab)

        self.diff_view.content_changed.connect(self._update_undo_redo_actions)

        self._update_undo_redo_actions()

    def _open_left_file(self):
        """Open a file for the left pane."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Left File", "", "All Files (*);;Text Files (*.txt);;Python Files (*.py)"
        )
        if file_path:
            self.diff_view.set_left_file(file_path)
            add_recent_file(self.config, file_path)
            self._update_recent_files_menu()
            self.status_bar.showMessage(f"Opened: {file_path}")

    def _open_right_file(self):
        """Open a file for the right pane."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Right File", "", "All Files (*);;Text Files (*.txt);;Python Files (*.py)"
        )
        if file_path:
            self.diff_view.set_right_file(file_path)
            add_recent_file(self.config, file_path)
            self._update_recent_files_menu()
            self.status_bar.showMessage(f"Opened: {file_path}")

    def _save_merged(self):
        """Save the merged result."""
        self.diff_view.save_merged()

    def _undo(self):
        """Undo the last action."""
        if self.diff_view.undo():
            undo_desc = self.diff_view.get_undo_description()
            self.status_bar.showMessage(f"Undo: {undo_desc}")

    def _redo(self):
        """Redo the last undone action."""
        if self.diff_view.redo():
            redo_desc = self.diff_view.get_redo_description()
            self.status_bar.showMessage(f"Redo: {redo_desc}")

    def _update_undo_redo_actions(self):
        """Update the enabled/disabled state of undo/redo actions."""
        can_undo = self.diff_view.can_undo()
        can_redo = self.diff_view.can_redo()
        self._actions["undo"].setEnabled(can_undo)
        self._actions["redo"].setEnabled(can_redo)

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

    def _toggle_folder_view(self, checked):
        """Toggle the folder comparison view."""
        pass

    def _compare_folders(self):
        """Open both left and right folders for comparison."""
        left_folder = QFileDialog.getExistingDirectory(
            self, "Select Left Folder", ""
        )

        if not left_folder:
            return

        right_folder = QFileDialog.getExistingDirectory(
            self, "Select Right Folder", ""
        )

        if not right_folder:
            return

        add_recent_folder(self.config, left_folder)
        add_recent_folder(self.config, right_folder)
        self._update_recent_folders_menu()

        self.status_bar.showMessage(f"Comparing folders: {left_folder} vs {right_folder}")

    def _show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About Merge & Diff Tool",
            "Merge & Diff Tool\n\n"
            "A WinMerge-like GUI tool for comparing and merging files.\n\n"
            "Features:\n"
            "- Side-by-side diff view\n"
            "- Inline character-level diff\n"
            "- Three-way merge for conflict resolution\n"
            "- File filters\n"
            "- Directory comparison\n\n"
            "Built with Python and PySide6."
        )

    def _open_three_way_merge(self):
        """Open three-way merge dialog."""
        base_path, _ = QFileDialog.getOpenFileName(
            self, "Select Base File (Optional)", "", "All Files (*)"
        )

        left_path, _ = QFileDialog.getOpenFileName(
            self, "Select Left File (Current/HEAD)", "", "All Files (*)"
        )

        if not left_path:
            return

        right_path, _ = QFileDialog.getOpenFileName(
            self, "Select Right File (Incoming)", "", "All Files (*)"
        )

        if not right_path:
            return

        if self._three_way_merge_view is None:
            self._three_way_merge_view = ThreeWayMergeView()
            self._three_way_merge_view.merge_complete.connect(self._on_merge_complete)

        self._three_way_merge_view.load_files(base_path, left_path, right_path)

        tab_index = self.tab_widget.addTab(
            self._three_way_merge_view,
            "3-Way Merge"
        )
        self.tab_widget.setCurrentIndex(tab_index)

        self.status_bar.showMessage(f"3-Way Merge: {left_path} vs {right_path}")

    def _on_merge_complete(self, file_path: str):
        """Handle merge completion."""
        QMessageBox.information(
            self, "Merge Complete",
            f"Merged file saved to: {file_path}"
        )

    def _toggle_inline_diff(self, checked):
        """Toggle inline character-level diff mode."""
        self.diff_view.set_inline_mode(checked)

    def _close_tab(self, index):
        """Close a tab."""
        widget = self.tab_widget.widget(index)
        if widget == self._three_way_merge_view:
            self._three_way_merge_view = None
        self.tab_widget.removeTab(index)

    def _update_recent_files_menu(self):
        """Update the recent files menu."""
        self.recent_files_menu.clear()
        self._recent_file_actions = []

        for file_path in self.config.recent_files:
            action = self.recent_files_menu.addAction(file_path)
            action.triggered.connect(lambda checked, path=file_path: self._open_recent_file(path))
            self._recent_file_actions.append(action)

        if not self._recent_file_actions:
            empty_action = self.recent_files_menu.addAction("(No recent files)")
            empty_action.setEnabled(False)

    def _update_recent_folders_menu(self):
        """Update the recent folders menu."""
        self.recent_folders_menu.clear()
        self._recent_folder_actions = []

        for folder_path in self.config.recent_folders:
            action = self.recent_folders_menu.addAction(folder_path)
            action.triggered.connect(lambda checked, path=folder_path: self._open_recent_folder(path))
            self._recent_folder_actions.append(action)

        if not self._recent_folder_actions:
            empty_action = self.recent_folders_menu.addAction("(No recent folders)")
            empty_action.setEnabled(False)

    def _open_recent_file(self, file_path: str):
        """Open a recent file."""
        if os.path.exists(file_path):
            self.diff_view.set_right_file(file_path)
            self.status_bar.showMessage(f"Opened: {file_path}")
        else:
            QMessageBox.warning(
                self, "File Not Found",
                f"File no longer exists: {file_path}"
            )
            if file_path in self.config.recent_files:
                self.config.recent_files.remove(file_path)
                save_config(self.config)
                self._update_recent_files_menu()

    def _open_recent_folder(self, folder_path: str):
        """Open a recent folder."""
        if os.path.exists(folder_path):
            self.status_bar.showMessage(f"Recent folder: {folder_path}")
        else:
            QMessageBox.warning(
                self, "Folder Not Found",
                f"Folder no longer exists: {folder_path}"
            )
            if folder_path in self.config.recent_folders:
                self.config.recent_folders.remove(folder_path)
                save_config(self.config)
                self._update_recent_folders_menu()

    def closeEvent(self, event):
        """Handle window close event."""
        self.config.window_width = self.width()
        self.config.window_height = self.height()
        self.config.window_x = self.x()
        self.config.window_y = self.y()
        self.config.window_maximized = self.isMaximized()
        save_config(self.config)
        self.diff_view.clear_history()
        super().closeEvent(event)
