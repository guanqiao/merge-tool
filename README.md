# Python Merge & Diff Tool

A WinMerge-like GUI tool for comparing and merging files and directories. Built with Python and PySide6.

## Features

### File Comparison
- **Side-by-side diff view**: Visual comparison of two files with synchronized scrolling
- **Inline character-level diff**: Toggle to see character-level differences within lines
- **Syntax highlighting**: Support for multiple programming languages
- **Line numbers**: Easy navigation with line number display
- **Color-coded differences**: Green for insertions, red for deletions, yellow for replacements

### Directory Comparison
- **Tree view comparison**: Side-by-side directory comparison
- **File filtering**: Filter files by patterns (include/exclude)
- **Custom filters**: Create and save custom file filters
- **Quick navigation**: Double-click files to compare them

### Merge Operations
- **Two-way merge**: Copy changes between left and right panels
- **Three-way merge**: Resolve Git merge conflicts with base/original reference
- **Conflict resolution**: Choose left, right, or both for each conflict
- **Save merged results**: Save merged content to new file

### Navigation & Search
- **Next/Previous difference**: Quick navigation between changes (F7/F8)
- **Copy left/right**: Copy selected or next change to the other side
- **Search within files**: Find text in compared files

### File History
- **Recent files**: Quick access to recently opened files
- **Recent folders**: Quick access to recently compared folders
- **Session persistence**: Window position and size saved between sessions

### Command Line Interface
Compare files directly from the terminal without opening the GUI:

```bash
# Compare two files
python main.py file1.txt file2.txt

# Compare two directories
python main.py dir1/ dir2/

# Generate patch file
python main.py --patch file1.txt file2.txt > diff.patch

# Output in JSON format
python main.py --json file1.txt file2.txt

# Output in unified diff format
python main.py --unified file1.txt file2.txt
```

### Advanced Features
- **Tabbed interface**: Multiple comparisons in separate tabs
- **Drag and drop**: Drag files/folders directly onto the application
- **Encoding support**: Automatic UTF-8 encoding detection
- **Patch generation**: Generate unified diff patches

## Requirements

- Python 3.8+
- PySide6 (LGPL license)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### GUI Mode
```bash
python main.py
```

### Command Line Mode
```bash
python main.py left_file right_file
python main.py left_folder right_folder
python main.py --patch file1.txt file2.txt
```

## Building Executable

To create a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile --name "MergeDiffTool" main.py
```

The executable will be in the `dist/` folder.

## Project Structure

```
merge_tool/
├── src/
│   ├── diff_engine.py         # Core diff algorithms
│   ├── gui/
│   │   ├── main_window.py     # Main application window
│   │   ├── diff_view.py       # Side-by-side diff view
│   │   ├── three_way_merge.py # Three-way merge UI
│   │   └── file_tree.py       # Directory comparison
│   └── utils/
│       ├── file_ops.py        # File operations
│       └── config.py          # Configuration & filters
├── tests/                     # Unit tests
├── docs/                      # Documentation
├── requirements.txt
├── README.md
├── main.py
└── pyinstaller_spec.py        # PyInstaller configuration
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+1 | Open Left File |
| Ctrl+2 | Open Right File |
| Ctrl+3 | Compare Folders |
| Ctrl+S | Save Merged |
| Ctrl+L | Copy to Left |
| Ctrl+R | Copy to Right |
| Ctrl+I | Toggle Inline Diff |
| Ctrl+M | 3-Way Merge |
| F7 | Previous Difference |
| F8 | Next Difference |
| Ctrl+Q | Exit |

## Configuration

Settings are stored in `~/.merge_tool/config.json`:
- Window position and size
- Recent files and folders
- Color theme settings
- File filters

## License

LGPL - Free for both commercial and non-commercial use.

## Comparison with WinMerge

This tool implements many WinMerge features including:

| Feature | WinMerge | MergeDiffTool |
|---------|----------|---------------|
| Side-by-side diff | ✓ | ✓ |
| Inline diff | ✓ | ✓ |
| Directory tree view | ✓ | ✓ |
| File filters | ✓ | ✓ |
| Three-way merge | ✓ | ✓ |
| Recent files | ✓ | ✓ |
| Command line | ✓ | ✓ |
| Tabbed interface | ✓ | ✓ |
| Patch generation | ✓ | ✓ |
| Image comparison | ✓ | ✗ |
| Binary/hex view | ✓ | ✗ |
| Plugin architecture | ✓ | ✗ |

Planned future enhancements:
- Image comparison
- Binary file hex view
- Plugin system for custom file types
- Shell context menu integration
