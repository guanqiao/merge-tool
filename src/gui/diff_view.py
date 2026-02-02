"""
Side-by-side diff view widget.

Provides a synchronized view of two files with diff highlighting.
"""

import logging
logger = logging.getLogger("MergeDiffTool.DiffView")

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QPlainTextEdit,
    QScrollBar, QFrame, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QEvent, QSize
from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QFont,
    QSyntaxHighlighter, QTextBlockUserData, QPainter
)
from src.diff_engine import DiffEngine, DiffResult, DiffType, InlineDiffResult, IgnoreOptions, LineAligner
from src.utils.file_ops import UndoRedoManager
from src.gui.syntax_highlighter import SyntaxHighlighter, detect_language_from_filename
from src.gui.search_bar import SearchBar, SearchHelper
from src.gui.connecting_lines import DiffConnectionLines
from src.utils.report_generator import ReportGenerator
from typing import List, Tuple


class LineNumberArea(QWidget):
    """Line number area for the text editor."""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class InlineDiffHighlighter(QSyntaxHighlighter):
    """Highlighter for inline character-level diffs."""

    COLORS = {
        DiffType.EQUAL: QColor("#ffffff"),
        DiffType.INSERT: QColor("#e6ffed"),
        DiffType.DELETE: QColor("#ffeef0"),
        DiffType.REPLACE: QColor("#fff5b1"),
    }

    INLINE_DELETE_COLOR = QColor("#ffcccc")
    INLINE_INSERT_COLOR = QColor("#ccffcc")

    def __init__(self, document, inline_diff_result: InlineDiffResult = None):
        super().__init__(document)
        self.inline_diff_result = inline_diff_result
        self._enabled = True

    def setEnabled(self, enabled: bool):
        """Enable or disable the highlighter."""
        self._enabled = enabled
        self.rehighlight()

    def isEnabled(self) -> bool:
        """Check if the highlighter is enabled."""
        return self._enabled

    def set_inline_diff_result(self, inline_diff_result: InlineDiffResult):
        """Set the inline diff result to highlight."""
        self.inline_diff_result = inline_diff_result
        self.rehighlight()

    def highlightBlock(self, text: str):
        """Highlight a block with inline character-level diffs."""
        if not self._enabled or not self.inline_diff_result:
            return

        block_num = self.currentBlock().blockNumber()
        lines = self.inline_diff_result.lines
        if block_num >= len(lines):
            return

        line = lines[block_num]

        if line.diff_type == DiffType.INSERT:
            delete_fmt = QTextCharFormat()
            delete_fmt.setBackground(self.INLINE_DELETE_COLOR)
            delete_fmt.setFontUnderline(True)
            delete_fmt.setUnderlineColor(QColor("#ff0000"))
            self.setFormat(0, len(text), delete_fmt)
            return

        if line.diff_type == DiffType.DELETE:
            delete_fmt = QTextCharFormat()
            delete_fmt.setBackground(self.INLINE_DELETE_COLOR)
            delete_fmt.setFontUnderline(True)
            delete_fmt.setUnderlineColor(QColor("#ff0000"))
            self.setFormat(0, len(text), delete_fmt)
            return

        if line.diff_type == DiffType.REPLACE:
            delete_ranges = []
            insert_ranges = []

            pos = 0
            char_diffs = DiffEngine.compare_char_level(line.left_text, line.right_text)

            for chunk_left, chunk_right, d_type in char_diffs:
                chunk_len = len(chunk_right) if chunk_right else len(chunk_left)

                if d_type == "replace":
                    delete_ranges.append((pos, pos + len(chunk_left)))
                    insert_ranges.append((pos, pos + len(chunk_right)))
                elif d_type == "delete":
                    delete_ranges.append((pos, pos + len(chunk_left)))
                elif d_type == "insert":
                    insert_ranges.append((pos, pos + len(chunk_right)))

                pos += chunk_len

            delete_ranges = self._merge_ranges(delete_ranges)
            insert_ranges = self._merge_ranges(insert_ranges)

            for start, end in delete_ranges:
                if start < len(text):
                    actual_start = min(start, len(text))
                    actual_end = min(end, len(text))
                    if actual_start < actual_end:
                        fmt = QTextCharFormat()
                        fmt.setBackground(self.INLINE_DELETE_COLOR)
                        fmt.setFontUnderline(True)
                        fmt.setUnderlineColor(QColor("#ff0000"))
                        self.setFormat(actual_start, actual_end - actual_start, fmt)

            for start, end in insert_ranges:
                if start < len(text):
                    actual_start = min(start, len(text))
                    actual_end = min(end, len(text))
                    if actual_start < actual_end:
                        fmt = QTextCharFormat()
                        fmt.setBackground(self.INLINE_INSERT_COLOR)
                        fmt.setFontUnderline(True)
                        fmt.setUnderlineColor(QColor("#00aa00"))
                        self.setFormat(actual_start, actual_end - actual_start, fmt)

    def _merge_ranges(self, ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Merge overlapping or adjacent ranges."""
        if not ranges:
            return []

        sorted_ranges = sorted(ranges, key=lambda x: x[0])
        merged = [sorted_ranges[0]]

        for start, end in sorted_ranges[1:]:
            last_start, last_end = merged[-1]
            if start <= last_end:
                merged[-1] = (last_start, max(last_end, end))
            else:
                merged.append((start, end))

        return merged


class DiffHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for diff output."""

    COLORS = {
        DiffType.EQUAL: QColor("#ffffff"),
        DiffType.INSERT: QColor("#e6ffed"),
        DiffType.DELETE: QColor("#ffeef0"),
        DiffType.REPLACE: QColor("#fff5b1"),
    }

    def __init__(self, document, diff_result: DiffResult = None):
        super().__init__(document)
        self.diff_result = diff_result
        self._inline_mode = False
        self._inline_result = None
        self._enabled = True

    def setEnabled(self, enabled: bool):
        """Enable or disable the highlighter."""
        self._enabled = enabled
        self.rehighlight()

    def isEnabled(self) -> bool:
        """Check if the highlighter is enabled."""
        return self._enabled

    def set_diff_result(self, diff_result: DiffResult):
        """Set the diff result to highlight."""
        self.diff_result = diff_result
        self._inline_mode = False
        self.rehighlight()

    def set_inline_diff_result(self, inline_result: InlineDiffResult):
        """Set the inline diff result for character-level highlighting."""
        self._inline_result = inline_result
        self._inline_mode = True
        self.rehighlight()

    def set_inline_mode(self, enabled: bool):
        """Enable or disable inline character-level diff mode."""
        self._inline_mode = enabled
        self.rehighlight()

    def is_inline_mode(self) -> bool:
        """Check if inline mode is enabled."""
        return self._inline_mode

    def highlightBlock(self, text: str):
        """Highlight a block of text based on diff type."""
        if self._inline_mode and self._inline_result:
            return

        if not self._enabled or not self.diff_result:
            return

        block_num = self.currentBlock().blockNumber()
        lines = self.diff_result.lines
        if block_num >= len(lines):
            return

        line = lines[block_num]
        if line.type != DiffType.EQUAL:
            fmt = QTextCharFormat()
            fmt.setBackground(self.COLORS.get(line.type, self.COLORS[DiffType.EQUAL]))
            self.setFormat(0, len(text), fmt)


class DiffTextEdit(QPlainTextEdit):
    """Custom text edit with line numbers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.syntax_highlighter = None

        self.update_line_number_area_width(0)
        self.setCenterOnScroll(True)

    def set_syntax_highlighting(self, language: str):
        """Enable syntax highlighting for the specified language."""
        if self.syntax_highlighter:
            self.syntax_highlighter.deleteLater()
        
        self.syntax_highlighter = SyntaxHighlighter(self.document(), language)

    def disable_syntax_highlighting(self):
        """Disable syntax highlighting."""
        if self.syntax_highlighter:
            self.syntax_highlighter.deleteLater()
            self.syntax_highlighter = None

    def set_diff_view(self, diff_view):
        """Set the parent DiffView reference for drag/drop handling."""
        self._diff_view = diff_view

    def dragEnterEvent(self, event):
        """Handle drag enter event for file drops."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        """Handle drop event for file drops."""
        if event.mimeData().hasUrls() and self._diff_view:
            event.acceptProposedAction()
            file_path = event.mimeData().urls()[0].toLocalFile()
            if file_path:
                if not self._diff_view._left_file_path:
                    self._diff_view.set_left_file(file_path)
                elif not self._diff_view._right_file_path:
                    self._diff_view.set_right_file(file_path)
                else:
                    self._diff_view.set_right_file(file_path)
        else:
            super().dropEvent(event)

    def line_number_area_width(self):
        """Calculate the width needed for line numbers."""
        digits = len(str(self.blockCount())) or 1
        return self.fontMetrics().horizontalAdvance("9") * digits + 10

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def line_number_area_paint_event(self, event):
        """Paint the line number area."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.black)
                painter.drawText(
                    0, top, self.line_number_area.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignRight, number
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        """Highlight the current line."""
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#ffffcc")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            cr.left(), cr.top(), self.line_number_area_width(), cr.height()
        )


class DiffView(QWidget):
    """Widget for displaying side-by-side file comparison."""

    file_loaded = Signal(str, str)
    content_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("DiffView.__init__ called")
        self._left_file_path = None
        self._right_file_path = None
        self._diff_result = None
        self._inline_diff_result = None
        self._left_content = ""
        self._right_content = ""
        self._merged_content = ""
        self._inline_mode = False
        self._undo_manager = UndoRedoManager()
        self._is_undo_redo_operation = False
        self._ignore_options = IgnoreOptions()
        self._diff_engine = DiffEngine(self._ignore_options)
        self._connecting_lines_enabled = False

        logger.debug("Calling _setup_ui...")
        self._setup_ui()
        logger.debug("Calling _setup_connections...")
        self._setup_connections()
        logger.debug("Calling _setup_drag_drop...")
        self._setup_drag_drop()
        logger.debug("DiffView initialization complete")

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.search_bar = SearchBar()
        self.search_bar.setVisible(False)
        layout.addWidget(self.search_bar)

        main_container = QWidget()
        main_layout = QHBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        left_frame = QFrame()
        left_layout = QHBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_editor = DiffTextEdit()
        self.left_editor.setReadOnly(False)
        self.left_highlighter = DiffHighlighter(self.left_editor.document())
        self.left_inline_highlighter = InlineDiffHighlighter(self.left_editor.document())
        left_layout.addWidget(self.left_editor)
        splitter.addWidget(left_frame)

        right_frame = QFrame()
        right_layout = QHBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_editor = DiffTextEdit()
        self.right_editor.setReadOnly(False)
        self.right_highlighter = DiffHighlighter(self.right_editor.document())
        self.right_inline_highlighter = InlineDiffHighlighter(self.right_editor.document())
        right_layout.addWidget(self.right_editor)
        splitter.addWidget(right_frame)

        main_layout.addWidget(splitter)
        layout.addWidget(main_container)

        self.connection_lines = DiffConnectionLines(main_container)
        self.connection_lines.setGeometry(main_container.rect())
        self.connection_lines.lower()

        self.left_editor.set_diff_view(self)
        self.right_editor.set_diff_view(self)

    def _setup_connections(self):
        """Set up signal/slot connections."""
        self.left_editor.verticalScrollBar().valueChanged.connect(
            self._sync_scroll
        )
        self.right_editor.verticalScrollBar().valueChanged.connect(
            self._sync_scroll
        )
        self.left_editor.textChanged.connect(self._on_left_content_changed)
        self.right_editor.textChanged.connect(self._on_right_content_changed)
        
        self.search_bar.search_requested.connect(self._on_search)
        self.search_bar.replace_requested.connect(self._on_replace)
        self.search_bar.replace_all_requested.connect(self._on_replace_all)
        self.search_bar.close_requested.connect(self._hide_search_bar)

    def _on_left_content_changed(self):
        """Handle left content changes."""
        if self._is_undo_redo_operation:
            return
        new_content = self.left_editor.toPlainText()
        if new_content != self._left_content:
            self._left_content = new_content
            self._create_snapshot("Edit Left")
            self.content_changed.emit()

    def _on_right_content_changed(self):
        """Handle right content changes."""
        if self._is_undo_redo_operation:
            return
        new_content = self.right_editor.toPlainText()
        if new_content != self._right_content:
            self._right_content = new_content
            self._create_snapshot("Edit Right")
            self.content_changed.emit()

    def _create_snapshot(self, description: str):
        """Create a snapshot for undo/redo."""
        self._undo_manager.snapshot(
            action_type="edit",
            left_content=self._left_content,
            right_content=self._right_content,
            description=description
        )

    def _setup_drag_drop(self):
        """Set up drag and drop support."""
        self.setAcceptDrops(True)

        self.left_editor.setAcceptDrops(True)
        self.right_editor.setAcceptDrops(True)

        self.left_editor.installEventFilter(self)
        self.right_editor.installEventFilter(self)

    def _sync_scroll(self, value):
        """Synchronize scrolling between left and right editors."""
        sender = self.sender()
        if sender == self.left_editor.verticalScrollBar():
            self.right_editor.verticalScrollBar().setValue(value)
        else:
            self.left_editor.verticalScrollBar().setValue(value)

    def set_left_file(self, file_path: str):
        """Set the left file to display."""
        self._left_file_path = file_path
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                self._left_content = f.read()
            self.left_editor.setPlainText(self._left_content)
            language = detect_language_from_filename(file_path)
            self.left_editor.set_syntax_highlighting(language)
            self._update_diff()
        except Exception as e:
            self.left_editor.setPlainText(f"Error reading file: {e}")

    def set_right_file(self, file_path: str):
        """Set the right file to display."""
        self._right_file_path = file_path
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                self._right_content = f.read()
            self.right_editor.setPlainText(self._right_content)
            language = detect_language_from_filename(file_path)
            self.right_editor.set_syntax_highlighting(language)
            self._update_diff()
        except Exception as e:
            self.right_editor.setPlainText(f"Error reading file: {e}")

    def compare_files(self, left_path: str, right_path: str):
        """Compare two files."""
        self._left_file_path = left_path
        self._right_file_path = right_path

        try:
            with open(left_path, "r", encoding="utf-8", errors="replace") as f:
                self._left_content = f.read()
        except Exception as e:
            self._left_content = f"Error reading file: {e}"

        try:
            with open(right_path, "r", encoding="utf-8", errors="replace") as f:
                self._right_content = f.read()
        except Exception as e:
            self._right_content = f"Error reading file: {e}"

        self.left_editor.setPlainText(self._left_content)
        self.right_editor.setPlainText(self._right_content)

        self._update_diff()

        self.file_loaded.emit(left_path, right_path)

    def _update_diff(self):
        """Update the diff highlighting."""
        if not self._left_content or not self._right_content:
            return

        self._diff_result = self._diff_engine.compare_text(
            self._left_content, self._right_content
        )

        self.left_highlighter.set_diff_result(self._diff_result)
        self.right_highlighter.set_diff_result(self._diff_result)

        self.connection_lines.set_diff_result(self._diff_result)
        self._update_connection_lines()

        if self._inline_mode:
            self._update_inline_diff()

    def _update_connection_lines(self):
        """Update connecting lines positions."""
        left_positions = []
        right_positions = []
        left_heights = []
        right_heights = []

        for i in range(self.left_editor.blockCount()):
            block = self.left_editor.document().findBlockByNumber(i)
            left_positions.append(self.left_editor.blockBoundingGeometry(block).y())
            left_heights.append(self.left_editor.blockBoundingRect(block).height())

        for i in range(self.right_editor.blockCount()):
            block = self.right_editor.document().findBlockByNumber(i)
            right_positions.append(self.right_editor.blockBoundingGeometry(block).y())
            right_heights.append(self.right_editor.blockBoundingRect(block).height())

        self.connection_lines.update_line_positions(left_positions, right_positions)
        self.connection_lines.update_line_heights(left_heights, right_heights)

    def set_connecting_lines_enabled(self, enabled: bool):
        """Enable or disable connecting lines."""
        self._connecting_lines_enabled = enabled
        self.connection_lines.set_visible(enabled)

    def set_ignore_whitespace(self, ignore: bool):
        """Set whether to ignore whitespace in comparisons."""
        self._ignore_options.ignore_whitespace = ignore
        self._diff_engine.set_ignore_options(self._ignore_options)
        self._update_diff()

    def set_ignore_case(self, ignore: bool):
        """Set whether to ignore case in comparisons."""
        self._ignore_options.ignore_case = ignore
        self._diff_engine.set_ignore_options(self._ignore_options)
        self._update_diff()

    def set_ignore_blank_lines(self, ignore: bool):
        """Set whether to ignore blank lines in comparisons."""
        self._ignore_options.ignore_blank_lines = ignore
        self._diff_engine.set_ignore_options(self._ignore_options)
        self._update_diff()

    def set_ignore_comments(self, ignore: bool):
        """Set whether to ignore comments in comparisons."""
        self._ignore_options.ignore_comments = ignore
        self._diff_engine.set_ignore_options(self._ignore_options)
        self._update_diff()

    def align_lines(self):
        """Align lines to improve diff accuracy."""
        if not self._diff_result:
            return

        left_lines = self._left_content.split('\n')
        right_lines = self._right_content.split('\n')

        aligned_result = LineAligner.align_lines(left_lines, right_lines, self._diff_result)
        self._diff_result = aligned_result

        self.left_highlighter.set_diff_result(self._diff_result)
        self.right_highlighter.set_diff_result(self._diff_result)

        self.connection_lines.set_diff_result(self._diff_result)
        self._update_connection_lines()

        if self._inline_mode:
            self._update_inline_diff()

    def get_ignore_options(self) -> IgnoreOptions:
        """Get current ignore options."""
        return self._ignore_options

    def set_syntax_highlighting_enabled(self, enabled: bool):
        """Enable or disable syntax highlighting."""
        if enabled:
            if self._left_file_path:
                language = detect_language_from_filename(self._left_file_path)
                self.left_editor.set_syntax_highlighting(language)
            if self._right_file_path:
                language = detect_language_from_filename(self._right_file_path)
                self.right_editor.set_syntax_highlighting(language)
        else:
            self.left_editor.disable_syntax_highlighting()
            self.right_editor.disable_syntax_highlighting()

    def show_search_bar(self):
        """Show the search bar."""
        self.search_bar.setVisible(True)
        self.search_bar.focus_find()

    def _hide_search_bar(self):
        """Hide the search bar."""
        self.search_bar.setVisible(False)

    def _on_search(self, search_text: str, case_sensitive: bool, 
                   whole_word: bool, use_regex: bool):
        """Handle search request."""
        pattern = SearchHelper.build_pattern(search_text, case_sensitive, 
                                          whole_word, use_regex)
        
        for editor in [self.left_editor, self.right_editor]:
            cursor = editor.textCursor()
            start_pos = cursor.position()
            text = editor.toPlainText()
            
            pos = SearchHelper.find_in_text(text, pattern, start_pos, forward=True)
            if pos == -1:
                pos = SearchHelper.find_in_text(text, pattern, 0, forward=True)
            
            if pos != -1:
                new_cursor = QTextCursor(editor.document())
                new_cursor.setPosition(pos)
                new_cursor.setPosition(pos + len(search_text), 
                                       QTextCursor.KeepAnchor)
                editor.setTextCursor(new_cursor)
                editor.setFocus()

    def _on_replace(self, find_text: str, replace_text: str):
        """Handle replace request."""
        pattern = SearchHelper.build_pattern(
            find_text, 
            self.search_bar.is_case_sensitive(),
            self.search_bar.is_whole_word(),
            self.search_bar.is_regex()
        )
        
        for editor in [self.left_editor, self.right_editor]:
            cursor = editor.textCursor()
            if cursor.hasSelection():
                selected_text = cursor.selectedText()
                if pattern.match(selected_text):
                    cursor.insertText(replace_text)
                    self._on_search(find_text, 
                                    self.search_bar.is_case_sensitive(),
                                    self.search_bar.is_whole_word(),
                                    self.search_bar.is_regex())

    def _on_replace_all(self, find_text: str, replace_text: str):
        """Handle replace all request."""
        pattern = SearchHelper.build_pattern(
            find_text, 
            self.search_bar.is_case_sensitive(),
            self.search_bar.is_whole_word(),
            self.search_bar.is_regex()
        )
        
        for editor in [self.left_editor, self.right_editor]:
            text = editor.toPlainText()
            new_text = SearchHelper.replace_in_text(text, pattern, replace_text)
            editor.setPlainText(new_text)

    def _update_inline_diff(self):
        """Update inline character-level diff highlighting."""
        if not self._left_content or not self._right_content:
            return

        self._inline_diff_result = InlineDiffResult.from_text(
            self._left_content, self._right_content
        )

        self.left_inline_highlighter.set_inline_diff_result(self._inline_diff_result)
        self.right_inline_highlighter.set_inline_diff_result(self._inline_diff_result)

    def set_inline_mode(self, enabled: bool):
        """Enable or disable inline character-level diff mode."""
        self._inline_mode = enabled
        if enabled:
            self.left_highlighter.setEnabled(False)
            self.right_highlighter.setEnabled(False)
            self.left_inline_highlighter.setEnabled(True)
            self.right_inline_highlighter.setEnabled(True)
            self._update_inline_diff()
        else:
            self.left_highlighter.setEnabled(True)
            self.right_highlighter.setEnabled(True)
            self.left_inline_highlighter.setEnabled(False)
            self.right_inline_highlighter.setEnabled(False)
            self.left_highlighter.set_diff_result(self._diff_result)
            self.right_highlighter.set_diff_result(self._diff_result)

    def is_inline_mode(self) -> bool:
        """Check if inline mode is enabled."""
        return self._inline_mode

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop event on the main diff view."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 2:
                left_path = urls[0].toLocalFile()
                right_path = urls[1].toLocalFile()
                self.compare_files(left_path, right_path)
            elif len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if not self._left_file_path:
                    self.set_left_file(file_path)
                elif not self._right_file_path:
                    self.set_right_file(file_path)
                else:
                    self.set_right_file(file_path)

    def eventFilter(self, obj, event):
        """Handle drag and drop events for the editors."""
        if event.type() == QEvent.DragEnter and event.mimeData().hasUrls():
            event.acceptProposedAction()
            return True
        elif event.type() == QEvent.Drop and event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if obj == self.left_editor:
                    self.set_left_file(file_path)
                elif obj == self.right_editor:
                    self.set_right_file(file_path)
            return True
        return super().eventFilter(obj, event)

    def copy_to_left(self):
        """Copy selected/next change from right to left."""
        if not self._diff_result:
            return

        self._create_snapshot("Copy to Left")

        cursor = self.right_editor.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor2 = self.left_editor.textCursor()
            cursor2.insertText(selected_text)
            self._left_content = self.left_editor.toPlainText()
        else:
            lines = self._right_content.split('\n')
            diff_lines = self._diff_result.lines
            for i, diff_line in enumerate(diff_lines):
                if diff_line.type in (DiffType.INSERT, DiffType.REPLACE):
                    if i < len(lines):
                        lines[i] = diff_line.content
                        self._left_content = '\n'.join(lines)
                        self.left_editor.setPlainText(self._left_content)
                        break

    def copy_all_to_left(self):
        """Copy all changes from right to left."""
        if not self._diff_result:
            return

        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self, "Confirm Copy All",
            "Copy all changes from right to left? This will overwrite all differences.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._create_snapshot("Copy All to Left")
            self._left_content = self._right_content
            self.left_editor.setPlainText(self._left_content)
            self._update_diff()

    def copy_to_right(self):
        """Copy selected/next change from left to right."""
        if not self._diff_result:
            return

        self._create_snapshot("Copy to Right")

        cursor = self.left_editor.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor2 = self.right_editor.textCursor()
            cursor2.insertText(selected_text)
            self._right_content = self.right_editor.toPlainText()
        else:
            lines = self._right_content.split('\n')
            diff_lines = self._diff_result.lines
            for i, diff_line in enumerate(diff_lines):
                if diff_line.type in (DiffType.DELETE, DiffType.REPLACE):
                    if i < len(lines):
                        left_line = diff_line.content
                        for j, dl in enumerate(diff_lines):
                            if dl.type == DiffType.REPLACE and j > i:
                                if j < len(lines):
                                    lines[i] = dl.content
                                break
                        else:
                            pass
                        self._right_content = '\n'.join(lines)
                        self.right_editor.setPlainText(self._right_content)
                        break

    def copy_all_to_right(self):
        """Copy all changes from left to right."""
        if not self._diff_result:
            return

        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self, "Confirm Copy All",
            "Copy all changes from left to right? This will overwrite all differences.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._create_snapshot("Copy All to Right")
            self._right_content = self._left_content
            self.right_editor.setPlainText(self._right_content)
            self._update_diff()

    def next_difference(self):
        """Navigate to the next difference."""
        if not self._diff_result:
            return

        diff_lines = self._diff_result.lines
        cursor = self.left_editor.textCursor()
        current_block = cursor.blockNumber()

        for i in range(current_block + 1, len(diff_lines)):
            if diff_lines[i].is_change:
                block = self.left_editor.document().firstBlock()
                for _ in range(i):
                    block = block.next()
                new_cursor = QTextCursor(block)
                self.left_editor.setTextCursor(new_cursor)

                block = self.right_editor.document().firstBlock()
                for _ in range(i):
                    block = block.next()
                new_cursor = QTextCursor(block)
                self.right_editor.setTextCursor(new_cursor)

                self.left_editor.setFocus()
                break

    def prev_difference(self):
        """Navigate to the previous difference."""
        if not self._diff_result:
            return

        diff_lines = self._diff_result.lines
        cursor = self.left_editor.textCursor()
        current_block = cursor.blockNumber()

        for i in range(current_block - 1, -1, -1):
            if diff_lines[i].is_change:
                block = self.left_editor.document().firstBlock()
                for _ in range(i):
                    block = block.next()
                new_cursor = QTextCursor(block)
                self.left_editor.setTextCursor(new_cursor)

                block = self.right_editor.document().firstBlock()
                for _ in range(i):
                    block = block.next()
                new_cursor = QTextCursor(block)
                self.right_editor.setTextCursor(new_cursor)

                self.left_editor.setFocus()
                break

    def save_merged(self):
        """Save the merged result to a file."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from PySide6.QtCore import QFileDevice

        merged_content = self._right_content

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged File", "", "All Files (*);;Text Files (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(merged_content)
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to save file: {e}"
                )

    def export_report(self, format: str):
        """Export diff report in specified format."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        if not self._diff_result:
            QMessageBox.warning(
                self, "No Diff", 
                "No diff to export. Please compare files first."
            )
            return

        format_map = {
            "html": ("HTML Report (*.html)", ".html"),
            "text": ("Text Report (*.txt)", ".txt"),
            "unified": ("Unified Diff (*.diff)", ".diff"),
            "json": ("JSON Report (*.json)", ".json")
        }

        if format not in format_map:
            QMessageBox.warning(
                self, "Invalid Format",
                f"Unknown format: {format}"
            )
            return

        filter_text, extension = format_map[format]
        default_name = f"diff_report{extension}"

        file_path, _ = QFileDialog.getSaveFileName(
            self, f"Export {format.upper()} Report",
            default_name,
            f"{filter_text};;All Files (*)"
        )

        if file_path:
            try:
                if format == "html":
                    report = ReportGenerator.generate_html_report(
                        self._diff_result,
                        self._left_file_path or "",
                        self._right_file_path or "",
                        self._left_content,
                        self._right_content
                    )
                elif format == "text":
                    report = ReportGenerator.generate_text_report(
                        self._diff_result,
                        self._left_file_path or "",
                        self._right_file_path or ""
                    )
                elif format == "unified":
                    report = ReportGenerator.generate_unified_diff_report(
                        self._diff_result,
                        self._left_file_path or "",
                        self._right_file_path or "",
                        self._left_content,
                        self._right_content
                    )
                elif format == "json":
                    report = ReportGenerator.generate_json_report(
                        self._diff_result,
                        self._left_file_path or "",
                        self._right_file_path or "",
                        self._left_content,
                        self._right_content
                    )

                if ReportGenerator.save_report(report, file_path):
                    QMessageBox.information(
                        self, "Export Successful",
                        f"Report saved to:\n{file_path}"
                    )
                else:
                    QMessageBox.critical(
                        self, "Export Failed",
                        "Failed to save report file."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error",
                    f"Error exporting report: {e}"
                )

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self._undo_manager.can_undo()

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self._undo_manager.can_redo()

    def undo(self) -> bool:
        """Undo the last action."""
        snapshot = self._undo_manager.undo()
        if snapshot:
            self._is_undo_redo_operation = True
            self._left_content = snapshot["left_content"]
            self._right_content = snapshot["right_content"]
            self.left_editor.setPlainText(self._left_content)
            self.right_editor.setPlainText(self._right_content)
            self._is_undo_redo_operation = False
            self._update_diff()
            self.content_changed.emit()
            return True
        return False

    def redo(self) -> bool:
        """Redo the last undone action."""
        snapshot = self._undo_manager.redo()
        if snapshot:
            self._is_undo_redo_operation = True
            self._left_content = snapshot["left_content"]
            self._right_content = snapshot["right_content"]
            self.left_editor.setPlainText(self._left_content)
            self.right_editor.setPlainText(self._right_content)
            self._is_undo_redo_operation = False
            self._update_diff()
            self.content_changed.emit()
            return True
        return False

    def get_undo_description(self) -> str:
        """Get description of the next action to undo."""
        return self._undo_manager.get_undo_description()

    def get_redo_description(self) -> str:
        """Get description of the next action to redo."""
        return self._undo_manager.get_redo_description()

    def clear_history(self):
        """Clear the undo/redo history."""
        self._undo_manager.clear()
