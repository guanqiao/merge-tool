"""
Connecting lines widget for visual diff connection.

Draws lines connecting differences between left and right panes.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QBrush
from typing import List, Tuple, Optional
from src.diff_engine import DiffResult, DiffType


class ConnectingLinesWidget(QWidget):
    """Widget for drawing connecting lines between diff panes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._diff_result: Optional[DiffResult] = None
        self._left_line_heights: List[int] = []
        self._right_line_heights: List[int] = []
        self._left_line_positions: List[int] = []
        self._right_line_positions: List[int] = []
        self._visible = True

        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def set_diff_result(self, diff_result: DiffResult):
        """Set the diff result for drawing connecting lines."""
        self._diff_result = diff_result
        self.update()

    def set_line_heights(self, left_heights: List[int], right_heights: List[int]):
        """Set line heights for both panes."""
        self._left_line_heights = left_heights
        self._right_line_heights = right_heights
        self.update()

    def set_line_positions(self, left_positions: List[int], right_positions: List[int]):
        """Set line positions (Y coordinates) for both panes."""
        self._left_line_positions = left_positions
        self._right_line_positions = right_positions
        self.update()

    def set_visible(self, visible: bool):
        """Set whether connecting lines are visible."""
        self._visible = visible
        self.update()

    def is_visible(self) -> bool:
        """Check if connecting lines are visible."""
        return self._visible

    def paintEvent(self, event):
        """Paint the connecting lines."""
        if not self._visible or not self._diff_result:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        left_width = self.width() // 2
        right_width = self.width() - left_width

        for i, line in enumerate(self._diff_result.lines):
            if line.type == DiffType.EQUAL:
                continue

            left_y = self._get_line_y(i, self._left_line_positions)
            right_y = self._get_line_y(i, self._right_line_positions)

            if left_y < 0 or right_y < 0:
                continue

            left_height = self._get_line_height(i, self._left_line_heights)
            right_height = self._get_line_height(i, self._right_line_heights)

            self._draw_connection(painter, left_width, left_y, left_height,
                              right_y, right_height, line.type)

    def _get_line_y(self, line_index: int, positions: List[int]) -> int:
        """Get Y position for a line."""
        if line_index < len(positions):
            return positions[line_index]
        return -1

    def _get_line_height(self, line_index: int, heights: List[int]) -> int:
        """Get height for a line."""
        if line_index < len(heights):
            return heights[line_index]
        return 20

    def _draw_connection(self, painter: QPainter, left_width: int,
                       left_y: int, left_height: int,
                       right_y: int, right_height: int,
                       diff_type: DiffType):
        """Draw a connection line between two panes."""
        left_x = left_width - 5
        right_x = left_width + 5

        color = self._get_color_for_diff_type(diff_type)
        pen = QPen(color, 2)
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)

        if diff_type == DiffType.INSERT:
            painter.drawLine(right_x, right_y, right_x, right_y + right_height)
            painter.drawLine(right_x, right_y + right_height // 2, 
                          left_x, right_y + right_height // 2)
        elif diff_type == DiffType.DELETE:
            painter.drawLine(left_x, left_y, left_x, left_y + left_height)
            painter.drawLine(left_x, left_y + left_height // 2, 
                          right_x, left_y + left_height // 2)
        elif diff_type == DiffType.REPLACE:
            left_center_y = left_y + left_height // 2
            right_center_y = right_y + right_height // 2
            
            painter.drawLine(left_x, left_y, left_x, left_y + left_height)
            painter.drawLine(right_x, right_y, right_x, right_y + right_height)
            
            painter.drawLine(left_x, left_center_y, right_x, right_center_y)

    def _get_color_for_diff_type(self, diff_type: DiffType) -> QColor:
        """Get color for a diff type."""
        color_map = {
            DiffType.INSERT: QColor("#00aa00"),
            DiffType.DELETE: QColor("#aa0000"),
            DiffType.REPLACE: QColor("#aa8800"),
        }
        return color_map.get(diff_type, QColor("#888888"))


class DiffConnectionLines(QWidget):
    """Container widget for connecting lines overlay."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connecting_lines = ConnectingLinesWidget(self)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI."""
        from PySide6.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._connecting_lines)

    def set_diff_result(self, diff_result: DiffResult):
        """Set the diff result."""
        self._connecting_lines.set_diff_result(diff_result)

    def update_line_positions(self, left_positions: List[int], 
                            right_positions: List[int]):
        """Update line positions."""
        self._connecting_lines.set_line_positions(left_positions, right_positions)

    def update_line_heights(self, left_heights: List[int], 
                           right_heights: List[int]):
        """Update line heights."""
        self._connecting_lines.set_line_heights(left_heights, right_heights)

    def set_visible(self, visible: bool):
        """Set visibility."""
        self._connecting_lines.set_visible(visible)
        self.setVisible(visible)

    def is_visible(self) -> bool:
        """Check if visible."""
        return self._connecting_lines.is_visible()

    def resizeEvent(self, event):
        """Handle resize event."""
        self._connecting_lines.setGeometry(self.rect())
        super().resizeEvent(event)