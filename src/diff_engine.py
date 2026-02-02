"""
Core diff engine implementing Myers diff algorithm.

Uses Python's difflib which implements the Myers algorithm
for computing the shortest edit script (SES) between two sequences.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional
import difflib


class DiffType(Enum):
    """Types of differences in a diff operation."""
    EQUAL = "equal"
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"


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
    def from_files(cls, left_lines: List[str], right_lines: List[str]) -> "DiffResult":
        """Create a DiffResult from two lists of lines."""
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
                # Count as changes for both sides
                for line in left_lines[i1:i2]:
                    diff_lines.append(DiffLine(
                        type=DiffType.REPLACE,
                        content=line,
                        left_line_num=left_count + 1
                    ))
                    left_count += 1
                    change_count += 1
                for line in right_lines[j1:j2]:
                    diff_lines.append(DiffLine(
                        type=DiffType.REPLACE,
                        content=line,
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
    def from_text(cls, left_text: str, right_text: str) -> "DiffResult":
        """Create a DiffResult from two text strings."""
        left_lines = left_text.splitlines(keepends=False)
        right_lines = right_text.splitlines(keepends=False)
        return cls.from_files(left_lines, right_lines)


class DiffEngine:
    """Core diff engine using Myers algorithm via difflib."""
    
    @staticmethod
    def compare_files(file1_path: str, file2_path: str) -> DiffResult:
        """Compare two files and return the diff result."""
        with open(file1_path, "r", encoding="utf-8", errors="replace") as f:
            left_lines = f.read().splitlines(keepends=False)
        
        with open(file2_path, "r", encoding="utf-8", errors="replace") as f:
            right_lines = f.read().splitlines(keepends=False)
        
        return DiffResult.from_files(left_lines, right_lines)
    
    @staticmethod
    def compare_text(text1: str, text2: str) -> DiffResult:
        """Compare two text strings and return the diff result."""
        return DiffResult.from_text(text1, text2)
    
    @staticmethod
    def compare_lines(lines1: List[str], lines2: List[str]) -> DiffResult:
        """Compare two lists of lines and return the diff result."""
        return DiffResult.from_files(lines1, lines2)
    
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
