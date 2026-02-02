"""
Three-way merge view widget for resolving merge conflicts.

Provides a three-pane view for base/original, left, and right files
similar to WinMerge's 3-way merge functionality for Git conflict resolution.
"""

import logging
logger = logging.getLogger("MergeDiffTool.ThreeWayMerge")

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QSplitter, QPlainTextEdit,
    QScrollBar, QFrame, QVBoxLayout, QLabel, QPushButton,
    QToolBar, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt, Signal, QEvent, QSize
from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QFont,
    QSyntaxHighlighter, QPainter
)
from src.diff_engine import DiffEngine, DiffResult, DiffType


class ThreeWayDiffHighlighter(QSyntaxHighlighter):
    """Highlighter for three-way merge diff output."""

    COLORS = {
        "base": QColor("#f0f0f0"),
        "left": QColor("#e6f7ff"),
        "right": QColor("#f6ffed"),
        "conflict_base": QColor("#fff0f0"),
        "conflict_left": QColor("#ffe6e6"),
        "conflict_right": QColor("#e6ffe6"),
        "resolved": QColor("#f5f5f5"),
    }

    def __init__(self, document, diff_result: DiffResult = None, side: str = "left"):
        super().__init__(document)
        self.diff_result = diff_result
        self.side = side

    def set_diff_result(self, diff_result: DiffResult):
        """Set the diff result to highlight."""
        self.diff_result = diff_result
        self.rehighlight()

    def set_side(self, side: str):
        """Set which side this highlighter is for."""
        self.side = side
        self.rehighlight()

    def highlightBlock(self, text: str):
        """Highlight a block of text based on diff type."""
        if not self.diff_result:
            return

        block_num = self.currentBlock().blockNumber()
        lines = self.diff_result.lines
        if block_num >= len(lines):
            return

        line = lines[block_num]
        color = self.COLORS.get("base")

        if self.side == "base":
            if line.type != DiffType.EQUAL:
                color = self.COLORS["conflict_base"]
        elif self.side == "left":
            if line.type in (DiffType.DELETE, DiffType.REPLACE):
                color = self.COLORS["conflict_left"]
            elif line.type == DiffType.INSERT:
                color = self.COLORS["left"]
        elif self.side == "right":
            if line.type in (DiffType.INSERT, DiffType.REPLACE):
                color = self.COLORS["conflict_right"]
            elif line.type == DiffType.DELETE:
                color = self.COLORS["right"]

        fmt = QTextCharFormat()
        fmt.setBackground(color)
        self.setFormat(0, len(text), fmt)


class ConflictMarker:
    """Represents a merge conflict marker."""

    CONFLICT_START = "<<<<<<< HEAD"
    CONFLICT_MIDDLE = "======="
    CONFLICT_END = ">>>>>>>"

    def __init__(self, start_line: int, end_line: int, left_content: str, right_content: str):
        self.start_line = start_line
        self.end_line = end_line
        self.left_content = left_content
        self.right_content = right_content
        self.resolution = None

    def has_resolution(self) -> bool:
        """Check if conflict has been resolved."""
        return self.resolution is not None


class ThreeWayMergeView(QWidget):
    """Widget for three-way merge conflict resolution."""

    merge_complete = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("ThreeWayMergeView.__init__ called")
        self._base_path = None
        self._left_path = None
        self._right_path = None
        self._base_content = ""
        self._left_content = ""
        self._right_content = ""
        self._merged_content = ""
        self._diff_result = None
        self._conflicts = []
        self._current_conflict_index = -1

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QToolBar()
        toolbar.setMovable(False)

        self.btn_use_left = QPushButton("Use Left")
        self.btn_use_left.setCheckable(True)
        toolbar.addWidget(self.btn_use_left)

        self.btn_use_right = QPushButton("Use Right")
        self.btn_use_right.setCheckable(True)
        toolbar.addWidget(self.btn_use_right)

        self.btn_use_both = QPushButton("Use Both")
        self.btn_use_both.setCheckable(True)
        toolbar.addWidget(self.btn_use_both)

        toolbar.addSeparator()

        self.btn_prev_conflict = QPushButton("Previous Conflict")
        toolbar.addWidget(self.btn_prev_conflict)

        self.btn_next_conflict = QPushButton("Next Conflict")
        toolbar.addWidget(self.btn_next_conflict)

        self.lbl_conflict_info = QLabel("No conflicts")
        toolbar.addWidget(self.lbl_conflict_info)

        layout.addWidget(toolbar)

        content_splitter = QSplitter(Qt.Horizontal)

        base_frame = QFrame()
        base_layout = QVBoxLayout(base_frame)
        base_layout.setContentsMargins(0, 0, 0, 0)
        base_label = QLabel("Base (Original)")
        base_label.setStyleSheet("font-weight: bold; padding: 2px; background-color: #f0f0f0;")
        base_layout.addWidget(base_label)
        self.base_editor = QPlainTextEdit()
        self.base_editor.setReadOnly(True)
        self.base_highlighter = ThreeWayDiffHighlighter(self.base_editor.document(), side="base")
        base_layout.addWidget(self.base_editor)
        content_splitter.addWidget(base_frame)

        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_label = QLabel("Left (Current/HEAD)")
        left_label.setStyleSheet("font-weight: bold; padding: 2px; background-color: #e6f7ff;")
        left_layout.addWidget(left_label)
        self.left_editor = QPlainTextEdit()
        self.left_editor.setReadOnly(True)
        self.left_highlighter = ThreeWayDiffHighlighter(self.left_editor.document(), side="left")
        left_layout.addWidget(self.left_editor)
        content_splitter.addWidget(left_frame)

        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_label = QLabel("Right (Incoming)")
        right_label.setStyleSheet("font-weight: bold; padding: 2px; background-color: #f6ffed;")
        right_layout.addWidget(right_label)
        self.right_editor = QPlainTextEdit()
        self.right_editor.setReadOnly(True)
        self.right_highlighter = ThreeWayDiffHighlighter(self.right_editor.document(), side="right")
        right_layout.addWidget(self.right_editor)
        content_splitter.addWidget(right_frame)

        result_frame = QFrame()
        result_layout = QVBoxLayout(result_frame)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_label = QLabel("Merged Result")
        result_label.setStyleSheet("font-weight: bold; padding: 2px; background-color: #f5f5f5;")
        result_layout.addWidget(result_label)
        self.result_editor = QPlainTextEdit()
        self.result_highlighter = ThreeWayDiffHighlighter(self.result_editor.document(), side="resolved")
        result_layout.addWidget(self.result_editor)
        content_splitter.addWidget(result_frame)

        content_splitter.setSizes([250, 250, 250, 250])
        layout.addWidget(content_splitter)

        self._button_group = QButtonGroup()
        self._button_group.addButton(self.btn_use_left)
        self._button_group.addButton(self.btn_use_right)
        self._button_group.addButton(self.btn_use_both)
        self._button_group.setExclusive(True)

    def _setup_connections(self):
        """Set up signal/slot connections."""
        self.btn_use_left.clicked.connect(self._use_left)
        self.btn_use_right.clicked.connect(self._use_right)
        self.btn_use_both.clicked.connect(self._use_both)
        self.btn_prev_conflict.clicked.connect(self._prev_conflict)
        self.btn_next_conflict.clicked.connect(self._next_conflict)

        self.left_editor.verticalScrollBar().valueChanged.connect(
            self._sync_scroll
        )
        self.right_editor.verticalScrollBar().valueChanged.connect(
            self._sync_scroll
        )
        self.base_editor.verticalScrollBar().valueChanged.connect(
            self._sync_scroll
        )
        self.result_editor.verticalScrollBar().valueChanged.connect(
            self._sync_scroll
        )

    def _sync_scroll(self, value):
        """Synchronize scrolling between all editors."""
        sender = self.sender()
        if sender == self.left_editor.verticalScrollBar():
            self.right_editor.verticalScrollBar().setValue(value)
            self.base_editor.verticalScrollBar().setValue(value)
            self.result_editor.verticalScrollBar().setValue(value)
        elif sender == self.right_editor.verticalScrollBar():
            self.left_editor.verticalScrollBar().setValue(value)
            self.base_editor.verticalScrollBar().setValue(value)
            self.result_editor.verticalScrollBar().setValue(value)
        elif sender == self.base_editor.verticalScrollBar():
            self.left_editor.verticalScrollBar().setValue(value)
            self.right_editor.verticalScrollBar().setValue(value)
            self.result_editor.verticalScrollBar().setValue(value)
        else:
            self.left_editor.verticalScrollBar().setValue(value)
            self.right_editor.verticalScrollBar().setValue(value)
            self.base_editor.verticalScrollBar().setValue(value)

    def load_files(self, base_path: str, left_path: str, right_path: str):
        """Load three files for three-way merge."""
        self._base_path = base_path
        self._left_path = left_path
        self._right_path = right_path

        self._base_content = self._read_file(base_path) if base_path else ""
        self._left_content = self._read_file(left_path)
        self._right_content = self._read_file(right_path)

        self.base_editor.setPlainText(self._base_content)
        self.left_editor.setPlainText(self._left_content)
        self.right_editor.setPlainText(self._right_content)

        self._generate_merged_content()
        self._detect_conflicts()
        self._update_diff()
        self._update_conflict_info()

    def _read_file(self, path: str) -> str:
        """Read file content."""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    def _generate_merged_content(self):
        """Generate initial merged content."""
        self._merged_content = self._left_content
        self.result_editor.setPlainText(self._merged_content)

    def _detect_conflicts(self):
        """Detect merge conflicts in the content."""
        self._conflicts = []
        lines = self._merged_content.split('\n')
        in_conflict = False
        conflict_start = -1
        left_lines = []
        right_lines = []

        for i, line in enumerate(lines):
            if line.startswith("<<<<<<<"):
                in_conflict = True
                conflict_start = i
                left_lines = []
                right_lines = []
            elif in_conflict and line.startswith("======="):
                pass
            elif in_conflict and line.startswith(">>>>>>>"):
                in_conflict = False
                conflict = ConflictMarker(
                    start_line=conflict_start,
                    end_line=i,
                    left_content='\n'.join(left_lines),
                    right_content='\n'.join(right_lines)
                )
                self._conflicts.append(conflict)
                left_lines = []
                right_lines = []
            elif in_conflict:
                if not line.startswith("======="):
                    if not line.startswith(">>>>>>>"):
                        if left_lines or not line.startswith("<<<<<<<"):
                            if not line.startswith("<<<<<<<"):
                                if not right_lines:
                                    if not line.startswith("======="):
                                        left_lines.append(line)
                                else:
                                    right_lines.append(line)
                            else:
                                left_lines.append(line.replace("<<<<<<< HEAD", "").strip())
                else:
                    pass

        self._current_conflict_index = -1 if not self._conflicts else 0

    def _update_diff(self):
        """Update diff highlighting for all panels."""
        self._diff_result = DiffEngine.compare_text(self._left_content, self._right_content)
        self.left_highlighter.set_diff_result(self._diff_result)
        self.right_highlighter.set_diff_result(self._diff_result)

    def _update_conflict_info(self):
        """Update the conflict info label."""
        if not self._conflicts:
            self.lbl_conflict_info.setText("No conflicts")
            self.btn_prev_conflict.setEnabled(False)
            self.btn_next_conflict.setEnabled(False)
        else:
            self.lbl_conflict_info.setText(
                f"Conflict {self._current_conflict_index + 1} of {len(self._conflicts)}"
            )
            self.btn_prev_conflict.setEnabled(self._current_conflict_index > 0)
            self.btn_next_conflict.setEnabled(self._current_conflict_index < len(self._conflicts) - 1)

    def _use_left(self):
        """Use left content for current conflict."""
        self._resolve_conflict("left")

    def _use_right(self):
        """Use right content for current conflict."""
        self._resolve_conflict("right")

    def _use_both(self):
        """Use both left and right content for current conflict."""
        self._resolve_conflict("both")

    def _resolve_conflict(self, resolution: str):
        """Resolve the current conflict."""
        if self._current_conflict_index < 0 or self._current_conflict_index >= len(self._conflicts):
            return

        conflict = self._conflicts[self._current_conflict_index]
        conflict.resolution = resolution

        lines = self._merged_content.split('\n')
        if resolution == "left":
            new_content = conflict.left_content
        elif resolution == "right":
            new_content = conflict.right_content
        else:
            new_content = conflict.left_content + '\n' + conflict.right_content

        if conflict.start_line < len(lines):
            lines[conflict.start_line:conflict.end_line + 1] = [new_content]

        self._merged_content = '\n'.join(lines)
        self.result_editor.setPlainText(self._merged_content)

        self._detect_conflicts()
        self._goto_conflict(min(self._current_conflict_index, len(self._conflicts) - 1))

    def _prev_conflict(self):
        """Go to previous conflict."""
        if self._current_conflict_index > 0:
            self._current_conflict_index -= 1
            self._goto_conflict(self._current_conflict_index)
            self._update_conflict_info()

    def _next_conflict(self):
        """Go to next conflict."""
        if self._current_conflict_index < len(self._conflicts) - 1:
            self._current_conflict_index += 1
            self._goto_conflict(self._current_conflict_index)
            self._update_conflict_info()

    def _goto_conflict(self, index: int):
        """Navigate to a specific conflict."""
        if index < 0 or index >= len(self._conflicts):
            return

        conflict = self._conflicts[index]
        block = self.result_editor.document().firstBlock()
        for _ in range(conflict.start_line):
            block = block.next()
        new_cursor = QTextCursor(block)
        self.result_editor.setTextCursor(new_cursor)
        self.result_editor.setFocus()

    def is_fully_resolved(self) -> bool:
        """Check if all conflicts have been resolved."""
        return all(c.has_resolution() for c in self._conflicts)

    def get_merged_content(self) -> str:
        """Get the current merged content."""
        return self._merged_content

    def save_merged(self, file_path: str):
        """Save the merged result to a file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self._merged_content)
            self.merge_complete.emit(file_path)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, "Error", f"Failed to save file: {e}"
            )

    def count_conflicts(self) -> int:
        """Return the number of conflicts."""
        return len(self._conflicts)

    def count_unresolved(self) -> int:
        """Return the number of unresolved conflicts."""
        return sum(1 for c in self._conflicts if not c.has_resolution())
