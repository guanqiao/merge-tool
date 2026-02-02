# Findings: Python Merge & Diff Tool

## Research Notes

### Diff Algorithms

#### Myers Diff Algorithm
- **Description**: Optimal O(ND) diff algorithm where N is sum of lengths, D is size of minimum edit script
- **Pros**: Optimal, widely used, well-tested
- **Cons**: Can be slower for very large files
- **Used in**: Git, WinMerge, Beyond Compare
- **Implementation**: Python's `difflib` uses a similar algorithm

### Python Libraries Available

1. **difflib** (built-in)
   - Standard library
   - Good for basic diffing
   - Limited for complex merge operations
   - Example: `difflib.unified_diff()`, `difflib.HtmlDiff()`

2. **python-magic**
   - File type detection
   - Useful for handling different file types

3. **Pygments** (optional)
   - Syntax highlighting
   - Can enhance the GUI

### GUI Frameworks Comparison

| Framework | Pros | Cons | Dependency |
|-----------|-------|-------|------------|
| **Tkinter** | Built-in, lightweight, cross-platform | Dated look, limited styling | None (stdlib) |
| **CustomTkinter** | Modern look, easy to use, built on Tkinter | Still somewhat limited | pip install customtkinter |
| **PyQt6** | Professional look, rich widgets, powerful | Heavy dependency (~50MB), steeper learning curve | pip install PyQt6 |
| **PySide6** | Similar to PyQt, LGPL license | Heavy dependency | pip install PySide6 |

### Feature Set for MVP

**Essential Features:**
- Side-by-side file comparison
- Visual highlighting of differences (added, removed, changed)
- Directory comparison
- Copy changes left/right
- Save merged result
- Navigate between differences

**Nice-to-have Features:**
- Syntax highlighting
- Line numbers
- File encoding detection
- Binary file detection
- Undo/redo
- Keyboard shortcuts
- Search functionality

### Existing Python Diff Tools

1. **Meld** (not Python-based, but good reference)
   - Feature-rich diff tool
   - Good UX patterns

2. **PyCharm Built-in Diff**
   - Clean, intuitive interface
   - Good color scheme

3. **VS Code Diff View**
   - Modern design
   - Good keyboard navigation

---

## Architecture Insights

### MVC Pattern Recommendation
- **Model**: Diff engine, file operations, state management
- **View**: All GUI components (Tkinter widgets)
- **Controller**: Main application logic, event handlers

### Key Components
1. **DiffEngine**: Handles diff algorithm execution
2. **DiffModel**: Stores diff results (diffs, line mappings)
3. **FileHandler**: Manages file I/O, encoding
4. **DiffView**: Side-by-side text display
5. **MergeController**: Handles merge actions

---

## Performance Considerations

- File reading: Use buffered reading for large files
- Diff calculation: Consider chunking for very large files
- GUI updates: Use threading for long operations
- Memory: Diff results can be large for big files

---

## Dependencies (Tentative)

```
customtkinter>=5.2.0  # For modern GUI
```

Optional:
```
pygments>=2.15.0     # For syntax highlighting
python-magic>=0.4.27 # For file type detection
```
