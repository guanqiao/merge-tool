"""
Configuration utilities for Merge & Diff Tool.

Provides file filter system, recent files/folders history,
and settings persistence similar to WinMerge.
"""

import os
import json
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class FileFilter:
    """Represents a file filter pattern."""
    name: str
    description: str
    include_patterns: List[str]
    exclude_patterns: List[str]
    is_default: bool = False

    @classmethod
    def default_text_filter(cls) -> "FileFilter":
        """Create default text file filter."""
        return cls(
            name="Text Files",
            description="Common text and source code files",
            include_patterns=[
                "*.txt", "*.md", "*.rst", "*.json", "*.xml", "*.yaml", "*.yml",
                "*.html", "*.htm", "*.css", "*.js", "*.ts", "*.py", "*.java",
                "*.c", "*.cpp", "*.h", "*.hpp", "*.cs", "*.go", "*.rs",
                "*.php", "*.rb", "*.swift", "*.kt", "*.lua", "*.sql"
            ],
            exclude_patterns=[],
            is_default=True
        )

    @classmethod
    def exclude_binary_filter(cls) -> "FileFilter":
        """Create filter to exclude binary files."""
        return cls(
            name="No Binary Files",
            description="Exclude binary files from comparison",
            include_patterns=[],
            exclude_patterns=[
                "*.exe", "*.dll", "*.so", "*.dylib", "*.bin", "*.o", "*.obj",
                "*.class", "*.jar", "*.pyc", "*.pyo", "*.pyd", "*.egg"
            ],
            is_default=False
        )

    @classmethod
    def python_only_filter(cls) -> "FileFilter":
        """Create Python-only filter."""
        return cls(
            name="Python Files",
            description="Python source files only",
            include_patterns=["*.py", "*.pyw"],
            exclude_patterns=["__pycache__", "*.pyc", "*.pyo", "*.egg-info"],
            is_default=False
        )

    def matches(self, file_path: str) -> bool:
        """Check if a file path matches this filter."""
        filename = os.path.basename(file_path)
        filename_lower = filename.lower()

        if self.exclude_patterns:
            for pattern in self.exclude_patterns:
                if self._match_pattern(pattern, filename_lower):
                    return False

        if self.include_patterns:
            for pattern in self.include_patterns:
                if self._match_pattern(pattern, filename_lower):
                    return True
            return False

        return True

    def _match_pattern(self, pattern: str, filename: str) -> bool:
        """Match a pattern against a filename."""
        if pattern.startswith("*"):
            return filename.endswith(pattern[1:])
        elif pattern.endswith("*"):
            return filename.startswith(pattern[:-1])
        else:
            return filename == pattern


@dataclass
class ThemeConfig:
    """Color theme configuration."""
    name: str = "Default"

    editor_bg: str = "#ffffff"
    editor_fg: str = "#000000"

    insert_bg: str = "#e6ffed"
    insert_fg: str = "#000000"

    delete_bg: str = "#ffeef0"
    delete_fg: str = "#000000"

    replace_bg: str = "#fff5b1"
    replace_fg: str = "#000000"

    equal_bg: str = "#ffffff"
    equal_fg: str = "#000000"

    current_line_bg: str = "#ffffcc"
    selection_bg: str = "#c0c0c0"

    line_number_fg: str = "#666666"
    line_number_bg: str = "#f0f0f0"

    tree_left_bg: str = "#e6f7ff"
    tree_right_bg: str = "#f6ffed"

    @classmethod
    def dark_theme(cls) -> "ThemeConfig":
        """Create dark theme configuration."""
        return cls(
            name="Dark",
            editor_bg="#1e1e1e",
            editor_fg="#d4d4d4",
            insert_bg="#203526",
            insert_fg="#b5cea8",
            delete_bg="#4a1a1a",
            delete_fg="#ce9178",
            replace_bg="#4a3b2a",
            replace_fg="#dcdcaa",
            equal_bg="#1e1e1e",
            equal_fg="#d4d4d4",
            current_line_bg="#2d2d2d",
            selection_bg="#264f78",
            line_number_fg="#858585",
            line_number_bg="#252526",
            tree_left_bg="#1a2a3a",
            tree_right_bg="#1a3a2a"
        )


@dataclass
class AppConfig:
    """Application configuration."""

    window_width: int = 1200
    window_height: int = 800
    window_x: int = 100
    window_y: int = 100
    window_maximized: bool = False

    recent_files: List[str] = field(default_factory=list)
    recent_folders: List[str] = field(default_factory=list)
    max_recent_items: int = 10

    default_encoding: str = "utf-8"
    auto_reload: bool = True
    show_line_numbers: bool = True
    highlight_current_line: bool = True

    color_equal: str = "#ffffff"
    color_insert: str = "#e6ffed"
    color_delete: str = "#ffeef0"
    color_replace: str = "#fff5b1"
    color_current_line: str = "#ffffcc"

    compare_directories_recursively: bool = True
    ignore_whitespace: bool = False
    ignore_empty_lines: bool = False
    case_sensitive: bool = True
    diff_context_lines: int = 3
    char_level_diff: bool = False

    custom_filters: List[dict] = field(default_factory=list)
    active_filter: Optional[str] = None

    theme: dict = field(default_factory=lambda: {
        "name": "Default",
        "editor_bg": "#ffffff",
        "editor_fg": "#000000",
        "insert_bg": "#e6ffed",
        "insert_fg": "#000000",
        "delete_bg": "#ffeef0",
        "delete_fg": "#000000",
        "replace_bg": "#fff5b1",
        "replace_fg": "#000000",
        "equal_bg": "#ffffff",
        "equal_fg": "#000000",
        "current_line_bg": "#ffffcc",
        "selection_bg": "#c0c0c0",
        "line_number_fg": "#666666",
        "line_number_bg": "#f0f0f0",
        "tree_left_bg": "#e6f7ff",
        "tree_right_bg": "#f6ffed"
    })

    tabbed_interface: bool = False
    confirm_exit: bool = True
    save_creates_backup: bool = True
    backup_extension: str = ".bak"


def get_config_path() -> str:
    """Get the path to the configuration file."""
    app_data_dir = os.path.join(os.path.expanduser("~"), ".merge_tool")
    os.makedirs(app_data_dir, exist_ok=True)
    return os.path.join(app_data_dir, "config.json")


def get_filters_path() -> str:
    """Get the path to the filters file."""
    app_data_dir = os.path.join(os.path.expanduser("~"), ".merge_tool")
    os.makedirs(app_data_dir, exist_ok=True)
    return os.path.join(app_data_dir, "filters.json")


def save_config(config: AppConfig) -> None:
    """Save configuration to file."""
    config_path = get_config_path()
    config_dict = {
        "window_width": config.window_width,
        "window_height": config.window_height,
        "window_x": config.window_x,
        "window_y": config.window_y,
        "window_maximized": config.window_maximized,
        "recent_files": config.recent_files[:config.max_recent_items],
        "recent_folders": config.recent_folders[:config.max_recent_items],
        "max_recent_items": config.max_recent_items,
        "default_encoding": config.default_encoding,
        "auto_reload": config.auto_reload,
        "show_line_numbers": config.show_line_numbers,
        "highlight_current_line": config.highlight_current_line,
        "color_equal": config.color_equal,
        "color_insert": config.color_insert,
        "color_delete": config.color_delete,
        "color_replace": config.color_replace,
        "color_current_line": config.color_current_line,
        "compare_directories_recursively": config.compare_directories_recursively,
        "ignore_whitespace": config.ignore_whitespace,
        "ignore_empty_lines": config.ignore_empty_lines,
        "case_sensitive": config.case_sensitive,
        "diff_context_lines": config.diff_context_lines,
        "char_level_diff": config.char_level_diff,
        "custom_filters": config.custom_filters,
        "active_filter": config.active_filter,
        "theme": config.theme,
        "tabbed_interface": config.tabbed_interface,
        "confirm_exit": config.confirm_exit,
        "save_creates_backup": config.save_creates_backup,
        "backup_extension": config.backup_extension,
    }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)


def load_config() -> AppConfig:
    """Load configuration from file."""
    config_path = get_config_path()

    if not os.path.exists(config_path):
        return AppConfig()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)

        return AppConfig(
            window_width=config_dict.get("window_width", 1200),
            window_height=config_dict.get("window_height", 800),
            window_x=config_dict.get("window_x", 100),
            window_y=config_dict.get("window_y", 100),
            window_maximized=config_dict.get("window_maximized", False),
            recent_files=config_dict.get("recent_files", []),
            recent_folders=config_dict.get("recent_folders", []),
            max_recent_items=config_dict.get("max_recent_items", 10),
            default_encoding=config_dict.get("default_encoding", "utf-8"),
            auto_reload=config_dict.get("auto_reload", True),
            show_line_numbers=config_dict.get("show_line_numbers", True),
            highlight_current_line=config_dict.get("highlight_current_line", True),
            color_equal=config_dict.get("color_equal", "#ffffff"),
            color_insert=config_dict.get("color_insert", "#e6ffed"),
            color_delete=config_dict.get("color_delete", "#ffeef0"),
            color_replace=config_dict.get("color_replace", "#fff5b1"),
            color_current_line=config_dict.get("color_current_line", "#ffffcc"),
            compare_directories_recursively=config_dict.get("compare_directories_recursively", True),
            ignore_whitespace=config_dict.get("ignore_whitespace", False),
            ignore_empty_lines=config_dict.get("ignore_empty_lines", False),
            case_sensitive=config_dict.get("case_sensitive", True),
            diff_context_lines=config_dict.get("diff_context_lines", 3),
            char_level_diff=config_dict.get("char_level_diff", False),
            custom_filters=config_dict.get("custom_filters", []),
            active_filter=config_dict.get("active_filter", None),
            theme=config_dict.get("theme", {"name": "Default"}),
            tabbed_interface=config_dict.get("tabbed_interface", False),
            confirm_exit=config_dict.get("confirm_exit", True),
            save_creates_backup=config_dict.get("save_creates_backup", True),
            backup_extension=config_dict.get("backup_extension", ".bak"),
        )
    except Exception:
        return AppConfig()


def save_filters(filters: List[FileFilter]) -> None:
    """Save custom file filters to file."""
    filters_path = get_filters_path()
    filters_data = []

    for f in filters:
        if not f.is_default:
            filters_data.append({
                "name": f.name,
                "description": f.description,
                "include_patterns": f.include_patterns,
                "exclude_patterns": f.exclude_patterns,
                "is_default": False
            })

    with open(filters_path, "w", encoding="utf-8") as f:
        json.dump(filters_data, f, indent=2)


def load_filters() -> List[FileFilter]:
    """Load custom file filters from file."""
    filters_path = get_filters_path()
    filters = [
        FileFilter.default_text_filter(),
        FileFilter.exclude_binary_filter(),
        FileFilter.python_only_filter()
    ]

    if not os.path.exists(filters_path):
        return filters

    try:
        with open(filters_path, "r", encoding="utf-8") as f:
            filters_data = json.load(f)

        for data in filters_data:
            filters.append(FileFilter(
                name=data["name"],
                description=data["description"],
                include_patterns=data.get("include_patterns", []),
                exclude_patterns=data.get("exclude_patterns", []),
                is_default=False
            ))
    except Exception:
        pass

    return filters


def add_recent_file(config: AppConfig, file_path: str) -> None:
    """Add a file to the recent files list."""
    if file_path in config.recent_files:
        config.recent_files.remove(file_path)
    config.recent_files.insert(0, file_path)
    config.recent_files = config.recent_files[:config.max_recent_items]
    save_config(config)


def add_recent_folder(config: AppConfig, folder_path: str) -> None:
    """Add a folder to the recent folders list."""
    if folder_path in config.recent_folders:
        config.recent_folders.remove(folder_path)
    config.recent_folders.insert(0, folder_path)
    config.recent_folders = config.recent_folders[:config.max_recent_items]
    save_config(config)
