"""
Side-by-side diff view widget.

Provides a synchronized view of two files with diff highlighting.
"""

import logging
logger = logging.getLogger("MergeDiffTool.DiffView")

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QSplitter, QPlainTextEdit,
    QScrollBar, QFrame
)
from PySide6.QtCore import Qt, Signal, QEvent, QSize
from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QFont,
    QSyntaxHighlighter, QTextBlockUserData, QPainter
)
from src.diff_engine import DiffEngine, DiffResult, DiffType


class LineNumberArea(QWidget):
    """Line number area for the text editor."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
    
    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class DiffHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for diff output."""
    
    # Color scheme for diff highlighting
    COLORS = {
        DiffType.EQUAL: QColor("#ffffff"),      # White (no highlight)
        DiffType.INSERT: QColor("#e6ffed"),     # Light green
        DiffType.DELETE: QColor("#ffeef0"),     # Light red
        DiffType.REPLACE: QColor("#fff5b1"),    # Light yellow
    }
    
    def __init__(self, document, diff_result: DiffResult = None):
        super().__init__(document)
        self.diff_result = diff_result
    
    def set_diff_result(self, diff_result: DiffResult):
        """Set the diff result to highlight."""
        self.diff_result = diff_result
        self.rehighlight()
    
    def highlightBlock(self, block_num: int):
        """Highlight a block of text based on diff type."""
        if not self.diff_result:
            return
        
        lines = self.diff_result.lines
        if block_num >= len(lines):
            return
        
        line = lines[block_num]
        fmt = QTextCharFormat()
        fmt.setBackground(self.COLORS.get(line.type, self.COLORS[DiffType.EQUAL]))
        self.setFormat(0, len(block.text()), fmt)


class DiffTextEdit(QPlainTextEdit):
    """Custom text edit with line numbers."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        self.update_line_number_area_width(0)
        self.setCenterOnScroll(True)
    
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
    
    file_loaded = Signal(str, str)  # Emitted when files are loaded
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("DiffView.__init__ called")
        self._left_file_path = None
        self._right_file_path = None
        self._diff_result = None
        self._left_content = ""
        self._right_content = ""
        self._merged_content = ""
        
        logger.debug("Calling _setup_ui...")
        self._setup_ui()
        logger.debug("Calling _setup_connections...")
        self._setup_connections()
        logger.debug("DiffView initialization complete")
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for left/right panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel
        left_frame = QFrame()
        left_layout = QHBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_editor = DiffTextEdit()
        self.left_editor.setReadOnly(True)
        self.left_highlighter = DiffHighlighter(self.left_editor.document())
        left_layout.addWidget(self.left_editor)
        splitter.addWidget(left_frame)
        
        # Right panel
        right_frame = QFrame()
        right_layout = QHBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_editor = DiffTextEdit()
        self.right_editor.setReadOnly(True)
        self.right_highlighter = DiffHighlighter(self.right_editor.document())
        right_layout.addWidget(self.right_editor)
        splitter.addWidget(right_frame)
        
        layout.addWidget(splitter)
    
    def _setup_connections(self):
        """Set up signal/slot connections."""
        # Connect scroll synchronization
        self.left_editor.verticalScrollBar().valueChanged.connect(
            self._sync_scroll
        )
        self.right_editor.verticalScrollBar().valueChanged.connect(
            self._sync_scroll
        )
    
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
            self._update_diff()
        except Exception as e:
            self.right_editor.setPlainText(f"Error reading file: {e}")
    
    def compare_files(self, left_path: str, right_path: str):
        """Compare two files."""
        self._left_file_path = left_path
        self._right_file_path = right_path
        
        # Read files
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
        
        # Update editors
        self.left_editor.setPlainText(self._left_content)
        self.right_editor.setPlainText(self._right_content)
        
        # Update diff highlighting
        self._update_diff()
        
        # Emit signal
        self.file_loaded.emit(left_path, right_path)
    
    def _update_diff(self):
        """Update the diff highlighting."""
        if not self._left_content or not self._right_content:
            return
        
        self._diff_result = DiffEngine.compare_text(
            self._left_content, self._right_content
        )
        
        self.left_highlighter.set_diff_result(self._diff_result)
        self.right_highlighter.set_diff_result(self._diff_result)
    
    def copy_to_left(self):
        """Copy selected/next change from right to left."""
        if not self._diff_result:
            return
        
        cursor = self.right_editor.textCursor()
        if cursor.hasSelection():
            # Copy selected text from right to left
            selected_text = cursor.selectedText()
            cursor2 = self.left_editor.textCursor()
            cursor2.insertText(selected_text)
            self._left_content = self.left_editor.toPlainText()
        else:
            # Copy next change from right to left
            lines = self._right_content.split('\n')
            diff_lines = self._diff_result.lines
            for i, diff_line in enumerate(diff_lines):
                if diff_line.type in (DiffType.INSERT, DiffType.REPLACE):
                    if i < len(lines):
                        lines[i] = diff_line.content
                        self._left_content = '\n'.join(lines)
                        self.left_editor.setPlainText(self._left_content)
                        break
    
    def copy_to_right(self):
        """Copy selected/next change from left to right."""
        if not self._diff_result:
            return
        
        cursor = self.left_editor.textCursor()
        if cursor.hasSelection():
            # Copy selected text from left to right
            selected_text = cursor.selectedText()
            cursor2 = self.right_editor.textCursor()
            cursor2.insertText(selected_text)
            self._right_content = self.right_editor.toPlainText()
        else:
            # Copy next change from left to right
            lines = self._right_content.split('\n')
            diff_lines = self._diff_result.lines
            for i, diff_line in enumerate(diff_lines):
                if diff_line.type in (DiffType.DELETE, DiffType.REPLACE):
                    if i < len(lines):
                        left_line = diff_line.content
                        # Find corresponding right line
                        for j, dl in enumerate(diff_lines):
                            if dl.type == DiffType.REPLACE and j > i:
                                # This is the replacement
                                if j < len(lines):
                                    lines[i] = dl.content
                                break
                        else:
                            # No replacement, use empty or original
                            pass
                        self._right_content = '\n'.join(lines)
                        self.right_editor.setPlainText(self._right_content)
                        break
    
    def next_difference(self):
        """Navigate to the next difference."""
        if not self._diff_result:
            return
        
        diff_lines = self._diff_result.lines
        cursor = self.left_editor.textCursor()
        current_block = cursor.blockNumber()
        
        for i in range(current_block + 1, len(diff_lines)):
            if diff_lines[i].is_change:
                # Move to this line in both editors
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
                # Move to this line in both editors
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
        
        # Determine which content to save (prefer right side as it's typically the "merged" result)
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
