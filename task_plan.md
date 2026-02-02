# Task Plan: Python Merge & Diff Tool (WinMerge-like)

## Goal
Create a Python-based merge and diff tool similar to WinMerge, with a graphical interface for comparing and merging files/directories.

## Status
| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Planning & Research | ✅ completed | PySide6 chosen, Myers algorithm confirmed |
| Phase 2: Project Setup | ✅ completed | Structure created, requirements defined |
| Phase 3: Core Diff Engine | ✅ completed | Myers algorithm, file/directory diff |
| Phase 4: GUI Implementation | ✅ completed | Main window, diff view, merge controls |
| Phase 5: File Operations | ✅ completed | I/O, merge save, backup, encoding, undo/redo |
| Phase 6: Testing & Documentation | ✅ completed | Tests, user guide, packaging config |

---

## Phase 1: Planning & Research (in_progress)

### Objectives
- Research existing diff algorithms (Myers, LCS)
- Choose GUI framework (Tkinter/PyQt/PySide)
- Define core features
- Design architecture

### Tasks
- [ ] Research diff algorithms
- [ ] Evaluate GUI frameworks
- [ ] Define feature set
- [ ] Create project structure

### Decisions
- **GUI Framework**: **PySide6** (LGPL license, professional features, excellent performance)
  - PySide6 chosen over PyQt6 due to LGPL license (free for proprietary use)
  - QPlainTextEdit for efficient large file handling
  - QSyntaxHighlighter for syntax highlighting
  - QFileSystemModel for directory tree view
- **Diff Algorithm**: Myers diff algorithm (standard for merge tools, O(ND) complexity)
- **Python Version**: 3.8+

---

## Phase 2: Project Setup

### Objectives
- Initialize git repository
- Create project structure
- Set up dependencies
- Create initial commit

### Tasks
- [ ] Initialize git repository
- [ ] Create directory structure
- [ ] Create requirements.txt
- [ ] Create README.md
- [ ] Make initial commit

### Directory Structure
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
├── tests/
│   ├── test_diff_engine.py
│   └── test_file_ops.py
├── requirements.txt
├── README.md
└── main.py                 # Entry point
```

---

## Phase 3: Core Diff Engine

### Objectives
- Implement diff algorithm (Myers)
- Create file comparison logic
- Create directory comparison logic
- Add line-by-line comparison

### Tasks
- [ ] Implement Myers diff algorithm
- [ ] Create file diff class
- [ ] Create directory diff class
- [ ] Add line comparison utilities
- [ ] Write unit tests

---

## Phase 4: GUI Implementation

### Objectives
- Create main application window
- Implement side-by-side diff view
- Add syntax highlighting
- Create merge interface
- Implement navigation

### Tasks
- [ ] Create main window layout
- [ ] Implement side-by-side view
- [ ] Add diff highlighting (additions/deletions/changes)
- [ ] Create merge controls (copy left/right)
- [ ] Add file/directory tree view
- [ ] Implement keyboard shortcuts
- [ ] Add status bar

---

## Phase 5: File Operations

### Objectives
- Implement file reading/writing
- Add merge functionality
- Create backup system
- Add file encoding handling

### Tasks
- [ ] Implement file I/O operations
- [ ] Add merge save functionality
- [ ] Create backup before merge
- [ ] Handle different encodings
- [ ] Add undo/redo support

---

## Phase 6: Testing & Documentation

### Objectives
- Test all features
- Create user documentation
- Add examples
- Package for distribution

### Tasks
- [ ] Complete test coverage
- [ ] Create user guide
- [ ] Add screenshots
- [ ] Create example usage
- [ ] Package as executable

---

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| | | |
| | | |
| | | |

---

## Key Decisions

1. **GUI Framework Decision**: PySide6 (LGPL license)
   - PySide6: LGPL license, free for proprietary applications, professional features
   - PyQt6: GPL license, requires commercial license for proprietary use
   - Tkinter: Built-in but poor performance with large files
   - CustomTkinter: Modern look but same Tkinter performance limitations

2. **Diff Algorithm**: Myers algorithm
    - Standard for merge tools (used by git, WinMerge, etc.)
    - Efficient O(ND) complexity where N = input size, D = edit distance
    - Python's difflib implements Myers algorithm (SequenceMatcher)
    - Well-documented and battle-tested

3. **Architecture**: MVC pattern
    - Model: Diff engine, file operations
    - View: GUI components (PySide6 widgets)
    - Controller: Main application logic
