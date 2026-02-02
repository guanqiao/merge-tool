"""
Core diff engine implementing Myers diff algorithm.

Uses Python's difflib which implements the Myers algorithm
for computing the shortest edit script (SES) between two sequences.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional, Dict
import difflib
import re


class DiffType(Enum):
    """Types of differences in a diff operation."""
    EQUAL = "equal"
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"


@dataclass
class IgnoreOptions:
    """Options for ignoring certain aspects during diff comparison."""
    ignore_whitespace: bool = False
    ignore_case: bool = False
    ignore_blank_lines: bool = False
    ignore_comments: bool = False
    
    def preprocess_line(self, line: str) -> str:
        """Preprocess a line based on ignore options."""
        if self.ignore_blank_lines and not line.strip():
            return ""
        
        processed = line
        
        if self.ignore_comments:
            processed = self._remove_comments(processed)
        
        if self.ignore_whitespace:
            processed = processed.strip()
        
        if self.ignore_case:
            processed = processed.lower()
        
        return processed
    
    @staticmethod
    def _remove_comments(line: str) -> str:
        """Remove common comment patterns from a line."""
        patterns = [
            r'//.*$',           # C/C++/Java/JS single line
            r'/\*.*?\*/',       # C/C++/Java block comments
            r'#.*$',             # Python/Shell single line
            r'--.*$',            # SQL single line
            r';.*$',             # Assembly/INI single line
            r'<!--.*?-->',       # HTML/XML comments
        ]
        
        result = line
        for pattern in patterns:
            result = re.sub(pattern, '', result, flags=re.DOTALL)
        
        return result


@dataclass
class DiffLine:
    """Represents a single line in a diff result."""
    type: DiffType
    content: str
    left_line_num: Optional[int] = None
    right_line_num: Optional[int] = None
    
    @property
    def is_change(self) -> bool:
        """Check if this line represents a change."""
        return self.type != DiffType.EQUAL


@dataclass
class DiffResult:
    """Result of a file diff operation."""
    lines: List[DiffLine]
    left_line_count: int
    right_line_count: int
    change_count: int
    
    @classmethod
    def from_files(cls, left_lines: List[str], right_lines: List[str], 
                   ignore_options: Optional[IgnoreOptions] = None) -> "DiffResult":
        """Create a DiffResult from two lists of lines."""
        if ignore_options:
            left_lines = [ignore_options.preprocess_line(line) for line in left_lines]
            right_lines = [ignore_options.preprocess_line(line) for line in right_lines]
        
        matcher = difflib.SequenceMatcher(None, left_lines, right_lines)
        diff_lines = []
        left_count = 0
        right_count = 0
        change_count = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for line in left_lines[i1:i2]:
                    diff_lines.append(DiffLine(
                        type=DiffType.EQUAL,
                        content=line,
                        left_line_num=left_count + 1 if line else None,
                        right_line_num=right_count + 1 if line else None
                    ))
                    left_count += 1 if line else 0
                    right_count += 1 if line else 0
            elif tag == "insert":
                for line in right_lines[j1:j2]:
                    diff_lines.append(DiffLine(
                        type=DiffType.INSERT,
                        content=line,
                        right_line_num=right_count + 1
                    ))
                    right_count += 1
                    change_count += 1
            elif tag == "delete":
                for line in left_lines[i1:i2]:
                    diff_lines.append(DiffLine(
                        type=DiffType.DELETE,
                        content=line,
                        left_line_num=left_count + 1
                    ))
                    left_count += 1
                    change_count += 1
            elif tag == "replace":
                max_lines = max(len(left_lines[i1:i2]), len(right_lines[j1:j2]))
                for idx in range(max_lines):
                    if idx < len(left_lines[i1:i2]):
                        diff_lines.append(DiffLine(
                            type=DiffType.REPLACE,
                            content=left_lines[i1 + idx],
                            left_line_num=left_count + 1
                        ))
                        left_count += 1
                    if idx < len(right_lines[j1:j2]):
                        diff_lines.append(DiffLine(
                            type=DiffType.REPLACE,
                            content=right_lines[j1 + idx],
                            right_line_num=right_count + 1
                        ))
                        right_count += 1
                change_count += 1
        
        return cls(
            lines=diff_lines,
            left_line_count=left_count,
            right_line_count=right_count,
            change_count=change_count
        )
    
    @classmethod
    def from_text(cls, left_text: str, right_text: str, 
                  ignore_options: Optional[IgnoreOptions] = None) -> "DiffResult":
        """Create a DiffResult from two text strings."""
        left_lines = left_text.splitlines(keepends=False)
        right_lines = right_text.splitlines(keepends=False)
        return cls.from_files(left_lines, right_lines, ignore_options)


class DiffEngine:
    """Core diff engine using Myers algorithm via difflib."""
    
    def __init__(self, ignore_options: Optional[IgnoreOptions] = None):
        """Initialize the diff engine with optional ignore options."""
        self.ignore_options = ignore_options
    
    def set_ignore_options(self, ignore_options: IgnoreOptions):
        """Set the ignore options for comparison."""
        self.ignore_options = ignore_options
    
    @staticmethod
    def compare_files(file1_path: str, file2_path: str, 
                     ignore_options: Optional[IgnoreOptions] = None) -> DiffResult:
        """Compare two files and return the diff result."""
        with open(file1_path, "r", encoding="utf-8", errors="replace") as f:
            left_lines = f.read().splitlines(keepends=False)
        
        with open(file2_path, "r", encoding="utf-8", errors="replace") as f:
            right_lines = f.read().splitlines(keepends=False)
        
        return DiffResult.from_files(left_lines, right_lines, ignore_options)
    
    def compare_text(self, text1: str, text2: str) -> DiffResult:
        """Compare two text strings and return the diff result."""
        return DiffResult.from_text(text1, text2, self.ignore_options)
    
    @staticmethod
    def compare_lines(lines1: List[str], lines2: List[str], 
                     ignore_options: Optional[IgnoreOptions] = None) -> DiffResult:
        """Compare two lists of lines and return the diff result."""
        return DiffResult.from_files(lines1, lines2, ignore_options)
    
    @staticmethod
    def get_unified_diff(
        lines1: List[str],
        lines2: List[str],
        fromfile: str = "",
        tofile: str = ""
    ) -> List[str]:
        """Get unified diff format between two sequences."""
        return list(difflib.unified_diff(
            lines1, lines2,
            fromfile=fromfile,
            tofile=tofile,
            lineterm=""
        ))
    
    @staticmethod
    def get_context_unified_diff(
        lines1: List[str],
        lines2: List[str],
        fromfile: str = "",
        tofile: str = "",
        n: int = 3
    ) -> List[str]:
        """Get unified diff format with specified context lines."""
        return list(difflib.unified_diff(
            lines1, lines2,
            fromfile=fromfile,
            tofile=tofile,
            n=n,
            lineterm=""
        ))

    @staticmethod
    def compare_char_level(text1: str, text2: str) -> List[Tuple[str, str, str]]:
        """Compare two texts at character level.

        Returns a list of tuples: (text1_chunk, text2_chunk, diff_type)
        diff_type can be 'equal', 'insert', 'delete', or 'replace'
        """
        char_diff = []
        matcher = difflib.SequenceMatcher(None, text1, text2)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            chunk1 = text1[i1:i2]
            chunk2 = text2[j1:j2]

            if tag == "equal":
                char_diff.append((chunk1, chunk2, "equal"))
            elif tag == "insert":
                char_diff.append(("", chunk2, "insert"))
            elif tag == "delete":
                char_diff.append((chunk1, "", "delete"))
            elif tag == "replace":
                char_diff.append((chunk1, chunk2, "replace"))

        return char_diff

    @staticmethod
    def compare_word_level(text1: str, text2: str) -> List[Tuple[str, str, str]]:
        """Compare two texts at word level.

        Returns a list of tuples: (text1_word, text2_word, diff_type)
        """
        import re

        word_pattern = re.compile(r'\s+|\w+|[^\w\s]')

        def split_words(text):
            return word_pattern.findall(text)

        words1 = split_words(text1)
        words2 = split_words(text2)

        word_diff = []
        matcher = difflib.SequenceMatcher(None, words1, words2)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            chunk1 = ''.join(words1[i1:i2])
            chunk2 = ''.join(words2[j1:j2])

            if tag == "equal":
                word_diff.append((chunk1, chunk2, "equal"))
            elif tag == "insert":
                word_diff.append(("", chunk2, "insert"))
            elif tag == "delete":
                word_diff.append((chunk1, "", "delete"))
            elif tag == "replace":
                word_diff.append((chunk1, chunk2, "replace"))

        return word_diff


@dataclass
class InlineDiffLine:
    """Represents a line with inline character-level diff info."""

    left_text: str
    right_text: str
    diff_type: DiffType
    left_inline_diffs: List[Tuple[int, int]] = field(default_factory=list)
    right_inline_diffs: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class InlineDiffResult:
    """Result of inline character-level diff."""

    lines: List[InlineDiffLine]
    left_line_count: int
    right_line_count: int
    change_count: int

    @classmethod
    def from_text(cls, left_text: str, right_text: str, 
                  ignore_options: Optional[IgnoreOptions] = None) -> "InlineDiffResult":
        """Create InlineDiffResult from two text strings."""
        left_lines = left_text.splitlines(keepends=False)
        right_lines = right_text.splitlines(keepends=False)

        return cls.from_lines(left_lines, right_lines, ignore_options)

    @classmethod
    def from_lines(cls, left_lines: List[str], right_lines: List[str],
                   ignore_options: Optional[IgnoreOptions] = None) -> "InlineDiffResult":
        """Create InlineDiffResult from two lists of lines."""
        if ignore_options:
            left_lines = [ignore_options.preprocess_line(line) for line in left_lines]
            right_lines = [ignore_options.preprocess_line(line) for line in right_lines]
        
        matcher = difflib.SequenceMatcher(None, left_lines, right_lines)
        diff_lines = []
        left_count = 0
        right_count = 0
        change_count = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for line in left_lines[i1:i2]:
                    diff_lines.append(InlineDiffLine(
                        left_text=line,
                        right_text=line,
                        diff_type=DiffType.EQUAL
                    ))
                    left_count += 1
                    right_count += 1
            elif tag == "insert":
                for line in right_lines[j1:j2]:
                    diff_lines.append(InlineDiffLine(
                        left_text="",
                        right_text=line,
                        diff_type=DiffType.INSERT
                    ))
                    right_count += 1
                    change_count += 1
            elif tag == "delete":
                for line in left_lines[i1:i2]:
                    diff_lines.append(InlineDiffLine(
                        left_text=line,
                        right_text="",
                        diff_type=DiffType.DELETE
                    ))
                    left_count += 1
                    change_count += 1
            elif tag == "replace":
                for idx, line in enumerate(left_lines[i1:i2]):
                    inline_diffs = []
                    if j1 + idx < len(right_lines):
                        right_line = right_lines[j1 + idx]
                        inline_result = DiffEngine.compare_char_level(line, right_line)
                        for d_idx, (l_chunk, r_chunk, d_type) in enumerate(inline_result):
                            if d_type == "replace":
                                pos = sum(len(c[0]) for c in inline_result[:d_idx])
                                inline_diffs.append((pos, pos + len(r_chunk)))

                    diff_lines.append(InlineDiffLine(
                        left_text=line,
                        right_text=right_lines[j1 + idx] if j1 + idx < len(right_lines) else "",
                        diff_type=DiffType.REPLACE,
                        left_inline_diffs=inline_diffs,
                        right_inline_diffs=inline_diffs
                    ))
                    left_count += 1
                    right_count += 1
                    change_count += 1

                if len(left_lines[i1:i2]) < len(right_lines[j1:j2]):
                    for line in right_lines[j1 + len(left_lines[i1:i2]):j2]:
                        diff_lines.append(InlineDiffLine(
                            left_text="",
                            right_text=line,
                            diff_type=DiffType.INSERT
                        ))
                        right_count += 1
                        change_count += 1

        return cls(
            lines=diff_lines,
            left_line_count=left_count,
            right_line_count=right_count,
            change_count=change_count
        )


@dataclass
class DirectoryDiffEntry:
    """Represents a single entry in a directory diff result."""
    name: str
    left_path: Optional[str]
    right_path: Optional[str]
    is_directory: bool
    is_modified: bool
    is_only_left: bool
    is_only_right: bool


@dataclass
class DirectoryDiffResult:
    """Result of a directory diff operation."""
    entries: List[DirectoryDiffEntry]
    left_path: str
    right_path: str
    
    @property
    def modified_count(self) -> int:
        """Return the count of modified files."""
        return sum(1 for e in self.entries if e.is_modified)
    
    @property
    def only_left_count(self) -> int:
        """Return the count of files only in left directory."""
        return sum(1 for e in self.entries if e.is_only_left)
    
    @property
    def only_right_count(self) -> int:
        """Return the count of files only in right directory."""
        return sum(1 for e in self.entries if e.is_only_right)
    
    @property
    def total_count(self) -> int:
        """Return the total count of entries."""
        return len(self.entries)


class DirectoryDiffEngine:
    """Engine for comparing directories."""
    
    @staticmethod
    def compare_directories(left_path: str, right_path: str) -> DirectoryDiffResult:
        """Compare two directories and return the diff result."""
        import os
        from src.utils.file_ops import read_file
        
        entries = []
        
        if not os.path.isdir(left_path) or not os.path.isdir(right_path):
            return DirectoryDiffResult(entries=[], left_path=left_path, right_path=right_path)
        
        # Get all items from both directories
        left_items = set(os.listdir(left_path))
        right_items = set(os.listdir(right_path))
        all_items = left_items | right_items
        
        for item in sorted(all_items):
            left_item_path = os.path.join(left_path, item) if left_path else item
            right_item_path = os.path.join(right_path, item) if right_path else item
            
            left_exists = os.path.exists(left_item_path)
            right_exists = os.path.exists(right_item_path)
            
            is_only_left = left_exists and not right_exists
            is_only_right = right_exists and not left_exists
            is_directory = False
            is_modified = False
            
            if left_exists and right_exists:
                is_directory = os.path.isdir(left_item_path)
                
                if not is_directory:
                    # Compare file contents
                    try:
                        left_content = read_file(left_item_path)
                        right_content = read_file(right_item_path)
                        is_modified = left_content != right_content
                    except Exception:
                        is_modified = True
            
            entries.append(DirectoryDiffEntry(
                name=item,
                left_path=left_item_path if left_exists else None,
                right_path=right_item_path if right_exists else None,
                is_directory=is_directory,
                is_modified=is_modified,
                is_only_left=is_only_left,
                is_only_right=is_only_right
            ))
        
        return DirectoryDiffResult(
            entries=entries,
            left_path=left_path,
            right_path=right_path
        )
    
    @staticmethod
    def get_modified_files(result: DirectoryDiffResult) -> List[Tuple[str, str]]:
        """Get list of modified file pairs from directory diff result."""
        modified = []
        for entry in result.entries:
            if entry.is_modified and entry.left_path and entry.right_path:
                modified.append((entry.left_path, entry.right_path))
        return modified
    
    @staticmethod
    def get_files_only_in_left(result: DirectoryDiffResult) -> List[str]:
        """Get list of files only in left directory."""
        return [entry.left_path for entry in result.entries if entry.is_only_left and entry.left_path]
    
    @staticmethod
    def get_files_only_in_right(result: DirectoryDiffResult) -> List[str]:
        """Get list of files only in right directory."""
        return [entry.right_path for entry in result.entries if entry.is_only_right and entry.right_path]
