# Python Merge & Diff Tool

A WinMerge-like GUI tool for comparing and merging files and directories.

## Features

- **File Comparison**: Side-by-side diff view with syntax highlighting
- **Directory Comparison**: Tree view for comparing directories
- **Merge Operations**: Copy changes left/right, merge all
- **Syntax Highlighting**: Support for multiple programming languages
- **Navigation**: Jump to next/previous difference
- **File Operations**: Save merged results with backup
- **Encoding Support**: Automatic encoding detection
- **Undo/Redo**: Full history support for merge operations

## Requirements

- Python 3.8+
- PySide6 (LGPL license)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Building Executable

To create a standalone executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller --onefile --name "MergeDiffTool" main.py

# Or use the spec file
pyinstaller merge_tool.spec
```

The executable will be in the `dist/` folder.

## Project Structure

```
merge_tool/
├── src/
│   ├── diff_engine.py      # Core diff algorithms
│   ├── gui/
│   │   ├── main_window.py  # Main application window
│   │   ├── diff_view.py    # Side-by-side diff view
│   │   ├── merge_view.py   # Merge interface
│   │   └── file_tree.py    # Directory comparison
│   └── utils/
│       ├── file_ops.py     # File operations
│       └── config.py       # Configuration
├── tests/                  # Unit tests
├── docs/                   # User guide
├── requirements.txt
├── README.md
├── main.py
└── pyinstaller_spec.py     # PyInstaller configuration
```

## License

LGPL - Free for both commercial and non-commercial use.
