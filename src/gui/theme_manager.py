"""
Theme management for the application.

Supports light and dark themes with customizable colors.
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication
from typing import Dict
import json
import os

class Theme:
    """Theme definition with color scheme."""

    def __init__(self, name: str, colors: Dict[str, str]):
        self.name = name
        self.colors = colors

    def to_dict(self) -> Dict:
        """Convert theme to dictionary."""
        return {
            "name": self.name,
            "colors": self.colors
        }

    @staticmethod
    def from_dict(data: Dict) -> 'Theme':
        """Create theme from dictionary."""
        return Theme(data["name"], data["colors"])


class ThemeManager(QObject):
    """Manages application themes."""

    theme_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._current_theme = None
        self._themes = {}
        self._theme_file = os.path.expanduser("~/.merge_tool/themes.json")
        self._init_themes()
        self._load_saved_theme()

    def _init_themes(self):
        """Initialize built-in themes."""
        self._themes = {
            "light": Theme("Light", {
                "window": "#ffffff",
                "window_text": "#000000",
                "base": "#ffffff",
                "base_text": "#000000",
                "alternate_base": "#f5f5f5",
                "tooltip_base": "#ffffdc",
                "tooltip_text": "#000000",
                "text": "#000000",
                "button": "#f0f0f0",
                "button_text": "#000000",
                "bright_text": "#ffffff",
                "link": "#0000ff",
                "highlight": "#0078d7",
                "highlighted_text": "#ffffff"
            }),
            "dark": Theme("Dark", {
                "window": "#2b2b2b",
                "window_text": "#ffffff",
                "base": "#1e1e1e",
                "base_text": "#ffffff",
                "alternate_base": "#2d2d2d",
                "tooltip_base": "#3c3c3c",
                "tooltip_text": "#ffffff",
                "text": "#ffffff",
                "button": "#3c3c3c",
                "button_text": "#ffffff",
                "bright_text": "#ffffff",
                "link": "#4a9eff",
                "highlight": "#0078d7",
                "highlighted_text": "#ffffff"
            }),
            "monokai": Theme("Monokai", {
                "window": "#272822",
                "window_text": "#f8f8f2",
                "base": "#1e1f1c",
                "base_text": "#f8f8f2",
                "alternate_base": "#3e3d32",
                "tooltip_base": "#49483e",
                "tooltip_text": "#f8f8f2",
                "text": "#f8f8f2",
                "button": "#3e3d32",
                "button_text": "#f8f8f2",
                "bright_text": "#f8f8f2",
                "link": "#66d9ef",
                "highlight": "#a6e22e",
                "highlighted_text": "#272822"
            }),
            "dracula": Theme("Dracula", {
                "window": "#282a36",
                "window_text": "#f8f8f2",
                "base": "#1e1f29",
                "base_text": "#f8f8f2",
                "alternate_base": "#44475a",
                "tooltip_base": "#44475a",
                "tooltip_text": "#f8f8f2",
                "text": "#f8f8f2",
                "button": "#44475a",
                "button_text": "#f8f8f2",
                "bright_text": "#f8f8f2",
                "link": "#8be9fd",
                "highlight": "#bd93f9",
                "highlighted_text": "#282a36"
            }),
            "nord": Theme("Nord", {
                "window": "#2e3440",
                "window_text": "#eceff4",
                "base": "#242933",
                "base_text": "#eceff4",
                "alternate_base": "#3b4252",
                "tooltip_base": "#3b4252",
                "tooltip_text": "#eceff4",
                "text": "#eceff4",
                "button": "#3b4252",
                "button_text": "#eceff4",
                "bright_text": "#eceff4",
                "link": "#88c0d0",
                "highlight": "#81a1c1",
                "highlighted_text": "#2e3440"
            })
        }

    def get_themes(self) -> Dict[str, Theme]:
        """Get all available themes."""
        return self._themes

    def get_theme(self, name: str) -> Theme:
        """Get a specific theme by name."""
        return self._themes.get(name, self._themes["light"])

    def get_current_theme(self) -> Theme:
        """Get the currently active theme."""
        if self._current_theme is None:
            self._current_theme = self._themes["light"]
        return self._current_theme

    def set_theme(self, name: str):
        """Set the current theme."""
        if name in self._themes:
            self._current_theme = self._themes[name]
            self._apply_theme(self._current_theme)
            self._save_theme(name)
            self.theme_changed.emit(name)

    def _apply_theme(self, theme: Theme):
        """Apply theme to application."""
        app = QApplication.instance()
        if app is None:
            return

        palette = QPalette()

        colors = theme.colors

        palette.setColor(QPalette.ColorRole.Window, QColor(colors["window"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["window_text"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(colors["base"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["alternate_base"]))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors["tooltip_base"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors["tooltip_text"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(colors["button"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["button_text"]))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(colors["bright_text"]))
        palette.setColor(QPalette.ColorRole.Link, QColor(colors["link"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["highlight"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors["highlighted_text"]))

        app.setPalette(palette)

    def _load_saved_theme(self):
        """Load saved theme from file."""
        try:
            if os.path.exists(self._theme_file):
                with open(self._theme_file, 'r') as f:
                    data = json.load(f)
                    theme_name = data.get("current_theme", "light")
                    if theme_name in self._themes:
                        self._current_theme = self._themes[theme_name]
                        self._apply_theme(self._current_theme)
        except Exception:
            pass

    def _save_theme(self, theme_name: str):
        """Save current theme to file."""
        try:
            os.makedirs(os.path.dirname(self._theme_file), exist_ok=True)
            with open(self._theme_file, 'w') as f:
                json.dump({"current_theme": theme_name}, f)
        except Exception:
            pass


_theme_manager = None

def get_theme_manager() -> ThemeManager:
    """Get the singleton theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
