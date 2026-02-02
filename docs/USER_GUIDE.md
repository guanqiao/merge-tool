# Merge & Diff Tool - User Guide

A WinMerge-like GUI tool for comparing and merging files and directories.

## Features

- **File Comparison**: Side-by-side diff view with syntax highlighting
- **Directory Comparison**: Tree view for comparing directories
- **Merge Operations**: Copy changes left/right, merge all
- **Syntax Highlighting**: Support for multiple programming languages
- **Navigation**: Jump to next/previous difference
- **File Operations**: Save merged results with backup
- **Encoding Support**: Automatic encoding detection for various file types

## Installation

### Prerequisites
- Python 3.8 or higher
- PySide6 (automatically installed with requirements)

### Setup

```bash
# Clone or navigate to the project directory
cd merge_tool

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Usage

### Opening Files

1. **File Menu** → Open Left / Open Right
2. **Keyboard Shortcuts**:
   - `Ctrl+1`: Open left file
   - `Ctrl+2`: Open right file

### Directory Comparison

1. **File Menu** → Open Left / Open Right
2. Select directories instead of files
3. Double-click files in the tree view to compare them
4. Color indicators:
   - Blue: Left (original) directory
   - Green: Right (modified) directory

### Navigating Differences

- **Next Difference**: `F8` or Edit Menu → Next Difference
- **Previous Difference**: `F7` or Edit Menu → Previous Difference

### Merging Changes

#### Copy Individual Changes
1. Navigate to a difference
2. **Copy to Left** (`Ctrl+L`): Copy right side to left
3. **Copy to Right** (`Ctrl+R`): Copy left side to right

#### Merge All and Save
1. Review all differences
2. **File Menu** → Save Merged (`Ctrl+S`)
3. Choose output location
4. Optional: Backup is automatically created if file exists

### Undo/Redo

- Undo last action: Available in Edit menu
- Redo last undone action: Available in Edit menu

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open Left File | Ctrl+1 |
| Open Right File | Ctrl+2 |
| Save Merged | Ctrl+S |
| Copy to Left | Ctrl+L |
| Copy to Right | Ctrl+R |
| Next Difference | F8 |
| Previous Difference | F7 |
| Exit | Ctrl+Q |

## File Encoding Support

The tool automatically detects and handles various file encodings:
- UTF-8 (with and without BOM)
- Latin-1 / ISO-8859-1
- Windows-1252
- GBK (Chinese)
- Shift_JIS (Japanese)
- EUC-KR (Korean)

## Backup System

When saving merged files:
- Backups are stored in `backups/` subdirectory
- Filename format: `filename.YYYYMMDD_HHMMSS.bak`
- Original file permissions are preserved

## Troubleshooting

### Large Files

The tool uses `QPlainTextEdit` for efficient handling of large files, but very large files (>10MB) may experience performance degradation.

### Encoding Issues

If you see replacement characters (�), try:
1. The file may have an unsupported encoding
2. Check if the file is binary (not text)
3. Report the issue if common encoding fails

## Technical Details

### Architecture

- **GUI Framework**: PySide6 (LGPL licensed)
- **Diff Algorithm**: Myers algorithm (via Python's difflib)
- **Pattern**: Model-View-Controller (MVC)

### File Structure

```
merge_tool/
├── src/
│   ├── diff_engine.py      # Core diff algorithms
│   ├── gui/
│   │   ├── main_window.py  # Main application window
│   │   ├── diff_view.py    # Side-by-side diff view
│   │   └── file_tree.py    # Directory comparison
│   └── utils/
│       ├── file_ops.py     # File operations
│       └── config.py       # Configuration
├── tests/                  # Unit tests
├── docs/                   # Documentation
└── requirements.txt        # Dependencies
```

## License

LGPL - Free for both commercial and non-commercial use.
