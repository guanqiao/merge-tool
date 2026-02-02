"""
Configuration utilities.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AppConfig:
    """Application configuration."""
    
    # Window settings
    window_width: int = 1200
    window_height: int = 800
    windowMaximized: bool = False
    
    # Recent files
    recent_files: List[str] = field(default_factory=list)
    max_recent_files: int = 10
    
    # Diff settings
    default_encoding: str = "utf-8"
    auto_reload: bool = True
    show_line_numbers: bool = True
    
    # Colors (hex format)
    color_equal: str = "#ffffff"
    color_insert: str = "#e6ffed"
    color_delete: str = "#ffeef0"
    color_replace: str = "#fff5b1"
    color_current_line: str = "#ffffcc"
    
    # Comparison settings
    compare_directories_recursively: bool = True
    ignore_whitespace: bool = False
    case_sensitive: bool = True


def get_config_path() -> str:
    """Get the path to the configuration file."""
    app_data_dir = os.path.join(os.path.expanduser("~"), ".merge_tool")
    os.makedirs(app_data_dir, exist_ok=True)
    return os.path.join(app_data_dir, "config.json")


def save_config(config: AppConfig) -> None:
    """Save configuration to file."""
    import json
    
    config_path = get_config_path()
    config_dict = {
        "window_width": config.window_width,
        "window_height": config.window_height,
        "windowMaximized": config.windowMaximized,
        "recent_files": config.recent_files[:config.max_recent_files],
        "max_recent_files": config.max_recent_files,
        "default_encoding": config.default_encoding,
        "auto_reload": config.auto_reload,
        "show_line_numbers": config.show_line_numbers,
        "color_equal": config.color_equal,
        "color_insert": config.color_insert,
        "color_delete": config.color_delete,
        "color_replace": config.color_replace,
        "color_current_line": config.color_current_line,
        "compare_directories_recursively": config.compare_directories_recursively,
        "ignore_whitespace": config.ignore_whitespace,
        "case_sensitive": config.case_sensitive,
    }
    
    with open(config_path, "w") as f:
        json.dump(config_dict, f, indent=2)


def load_config() -> AppConfig:
    """Load configuration from file."""
    import json
    
    config_path = get_config_path()
    
    if not os.path.exists(config_path):
        return AppConfig()
    
    try:
        with open(config_path, "r") as f:
            config_dict = json.load(f)
        
        return AppConfig(
            window_width=config_dict.get("window_width", 1200),
            window_height=config_dict.get("window_height", 800),
            windowMaximized=config_dict.get("windowMaximized", False),
            recent_files=config_dict.get("recent_files", []),
            max_recent_files=config_dict.get("max_recent_files", 10),
            default_encoding=config_dict.get("default_encoding", "utf-8"),
            auto_reload=config_dict.get("auto_reload", True),
            show_line_numbers=config_dict.get("show_line_numbers", True),
            color_equal=config_dict.get("color_equal", "#ffffff"),
            color_insert=config_dict.get("color_insert", "#e6ffed"),
            color_delete=config_dict.get("color_delete", "#ffeef0"),
            color_replace=config_dict.get("color_replace", "#fff5b1"),
            color_current_line=config_dict.get("color_current_line", "#ffffcc"),
            compare_directories_recursively=config_dict.get("compare_directories_recursively", True),
            ignore_whitespace=config_dict.get("ignore_whitespace", False),
            case_sensitive=config_dict.get("case_sensitive", True),
        )
    except Exception:
        return AppConfig()
