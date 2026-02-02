"""
Tests for the diff engine.
"""

import pytest
import os
import tempfile
from src.diff_engine import DiffEngine, DiffResult, DiffType, DiffLine
from src.diff_engine import DirectoryDiffEngine, DirectoryDiffEntry, DirectoryDiffResult


class TestDiffEngine:
    """Test cases for the DiffEngine class."""
    
    def test_compare_identical_files(self):
        """Test comparing identical files."""
        lines1 = ["line1", "line2", "line3"]
        lines2 = ["line1", "line2", "line3"]
        
        result = DiffEngine.compare_lines(lines1, lines2)
        
        assert result.change_count == 0
        assert len(result.lines) == 3
        assert all(line.type == DiffType.EQUAL for line in result.lines)
    
    def test_compare_different_files(self):
        """Test comparing files with differences."""
        lines1 = ["line1", "line2", "line3"]
        lines2 = ["line1", "modified", "line3"]
        
        result = DiffEngine.compare_lines(lines1, lines2)
        
        assert result.change_count > 0
        assert len(result.lines) == 4
    
    def test_compare_with_insertions(self):
        """Test comparing with insertions."""
        lines1 = ["line1", "line2"]
        lines2 = ["line1", "line2", "line3", "line4"]
        
        result = DiffEngine.compare_lines(lines1, lines2)
        
        assert result.change_count == 2
        assert any(line.type == DiffType.INSERT for line in result.lines)
    
    def test_compare_with_deletions(self):
        """Test comparing with deletions."""
        lines1 = ["line1", "line2", "line3", "line4"]
        lines2 = ["line1", "line2"]
        
        result = DiffEngine.compare_lines(lines1, lines2)
        
        assert result.change_count == 2
        assert any(line.type == DiffType.DELETE for line in result.lines)
    
    def test_compare_empty_files(self):
        """Test comparing empty files."""
        result = DiffEngine.compare_lines([], [])
        
        assert result.change_count == 0
        assert len(result.lines) == 0
    
    def test_compare_text(self):
        """Test comparing text strings."""
        text1 = "hello\nworld"
        text2 = "hello\npython"
        
        result = DiffEngine.compare_text(text1, text2)
        
        assert result.change_count > 0
    
    def test_get_unified_diff(self):
        """Test getting unified diff format."""
        lines1 = ["line1", "line2", "line3"]
        lines2 = ["line1", "modified", "line3"]
        
        diff = DiffEngine.get_unified_diff(lines1, lines2, "old.txt", "new.txt")
        
        assert len(diff) > 0
        assert any("@@" in line for line in diff)
    
    def test_is_change_property(self):
        """Test the is_change property of DiffLine."""
        equal_line = DiffLine(type=DiffType.EQUAL, content="test")
        insert_line = DiffLine(type=DiffType.INSERT, content="test")
        
        assert not equal_line.is_change
        assert insert_line.is_change


class TestDiffResult:
    """Test cases for the DiffResult class."""
    
    def test_from_files_basic(self):
        """Test creating DiffResult from file content."""
        left = ["a", "b", "c"]
        right = ["a", "x", "c"]
        
        result = DiffResult.from_files(left, right)
        
        assert result.left_line_count == 3
        assert result.right_line_count == 3
        assert result.change_count == 1


class TestDirectoryDiffEngine:
    """Test cases for DirectoryDiffEngine."""
    
    def test_compare_identical_directories(self):
        """Test comparing identical directories."""
        with tempfile.TemporaryDirectory() as dir1, \
             tempfile.TemporaryDirectory() as dir2:
            
            # Create same files
            with open(os.path.join(dir1, "file.txt"), "w") as f:
                f.write("same content")
            with open(os.path.join(dir2, "file.txt"), "w") as f:
                f.write("same content")
            
            result = DirectoryDiffEngine.compare_directories(dir1, dir2)
            
            assert result.total_count == 1
            assert result.modified_count == 0
            assert result.only_left_count == 0
            assert result.only_right_count == 0
    
    def test_compare_directories_with_differences(self):
        """Test comparing directories with modifications."""
        with tempfile.TemporaryDirectory() as dir1, \
             tempfile.TemporaryDirectory() as dir2:
            
            # Create different files
            with open(os.path.join(dir1, "file.txt"), "w") as f:
                f.write("original")
            with open(os.path.join(dir2, "file.txt"), "w") as f:
                f.write("modified")
            
            result = DirectoryDiffEngine.compare_directories(dir1, dir2)
            
            assert result.modified_count == 1
    
    def test_compare_directories_with_new_files(self):
        """Test comparing directories with new files."""
        with tempfile.TemporaryDirectory() as dir1, \
             tempfile.TemporaryDirectory() as dir2:
            
            # Create file only in left
            with open(os.path.join(dir1, "left_only.txt"), "w") as f:
                f.write("content")
            
            # Create file only in right
            with open(os.path.join(dir2, "right_only.txt"), "w") as f:
                f.write("content")
            
            result = DirectoryDiffEngine.compare_directories(dir1, dir2)
            
            assert result.only_left_count == 1
            assert result.only_right_count == 1
    
    def test_compare_directories_with_subdirectories(self):
        """Test comparing directories with subdirectories."""
        with tempfile.TemporaryDirectory() as dir1, \
             tempfile.TemporaryDirectory() as dir2:
            
            # Create subdirectory in both
            os.makedirs(os.path.join(dir1, "subdir"))
            os.makedirs(os.path.join(dir2, "subdir"))
            
            result = DirectoryDiffEngine.compare_directories(dir1, dir2)
            
            # Subdirectory should be in results
            subdir_entry = next((e for e in result.entries if e.name == "subdir"), None)
            assert subdir_entry is not None
            assert subdir_entry.is_directory
    
    def test_get_modified_files(self):
        """Test getting list of modified files."""
        with tempfile.TemporaryDirectory() as dir1, \
             tempfile.TemporaryDirectory() as dir2:
            
            with open(os.path.join(dir1, "file.txt"), "w") as f:
                f.write("original")
            with open(os.path.join(dir2, "file.txt"), "w") as f:
                f.write("modified")
            
            result = DirectoryDiffEngine.compare_directories(dir1, dir2)
            modified = DirectoryDiffEngine.get_modified_files(result)
            
            assert len(modified) == 1
            left_path, right_path = modified[0]
            assert left_path.endswith("file.txt")
            assert right_path.endswith("file.txt")
    
    def test_get_files_only_in_left(self):
        """Test getting files only in left directory."""
        with tempfile.TemporaryDirectory() as dir1, \
             tempfile.TemporaryDirectory() as dir2:
            
            with open(os.path.join(dir1, "only_left.txt"), "w") as f:
                f.write("content")
            
            result = DirectoryDiffEngine.compare_directories(dir1, dir2)
            only_left = DirectoryDiffEngine.get_files_only_in_left(result)
            
            assert len(only_left) == 1
            assert only_left[0].endswith("only_left.txt")
    
    def test_get_files_only_in_right(self):
        """Test getting files only in right directory."""
        with tempfile.TemporaryDirectory() as dir1, \
             tempfile.TemporaryDirectory() as dir2:
            
            with open(os.path.join(dir2, "only_right.txt"), "w") as f:
                f.write("content")
            
            result = DirectoryDiffEngine.compare_directories(dir1, dir2)
            only_right = DirectoryDiffEngine.get_files_only_in_right(result)
            
            assert len(only_right) == 1
            assert only_right[0].endswith("only_right.txt")
