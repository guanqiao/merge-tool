"""
Tests for file operations utilities.
"""

import pytest
import os
import tempfile
from src.utils.file_ops import (
    read_file, write_file, create_backup, 
    get_file_info, compare_directories,
    read_file_with_encoding_detection, write_file_with_encoding,
    merge_files, UndoRedoManager, MergeResult
)


class TestFileOperations:
    """Test cases for file operations."""
    
    def test_read_write_file(self):
        """Test reading and writing files."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
            f.write("test content")
        
        try:
            content = read_file(temp_path)
            assert content == "test content"
        finally:
            os.unlink(temp_path)
    
    def test_read_file_encoding(self):
        """Test reading files with different encodings."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
            f.write("hello world")
        
        try:
            content = read_file(temp_path, encoding="utf-8")
            assert content == "hello world"
        finally:
            os.unlink(temp_path)
    
    def test_create_backup(self):
        """Test creating file backups."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
            f.write("original content")
        
        try:
            backup_path = create_backup(temp_path)
            
            assert os.path.exists(backup_path)
            assert backup_path != temp_path
            
            # Verify backup content
            backup_content = read_file(backup_path)
            assert backup_content == "original content"
            
            # Cleanup
            os.unlink(backup_path)
            os.unlink(temp_path)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_file_info(self):
        """Test getting file information."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
            f.write("test")
        
        try:
            info = get_file_info(temp_path)
            
            assert info["path"] == temp_path
            assert info["is_file"] == True
            assert info["is_dir"] == False
            assert info["size"] == 4
        finally:
            os.unlink(temp_path)
    
    def test_get_file_info_nonexistent(self):
        """Test getting info for non-existent file."""
        info = get_file_info("/nonexistent/path/file.txt")
        
        assert info["is_file"] == False
        assert info["is_dir"] == False
        assert info["size"] == 0
    
    def test_compare_identical_directories(self):
        """Test comparing identical directories."""
        with tempfile.TemporaryDirectory() as dir1, \
             tempfile.TemporaryDirectory() as dir2:
            
            # Create same files in both directories
            with open(os.path.join(dir1, "file1.txt"), "w") as f:
                f.write("content1")
            with open(os.path.join(dir2, "file1.txt"), "w") as f:
                f.write("content1")
            
            result = compare_directories(dir1, dir2)
            
            assert len(result["only_in_left"]) == 0
            assert len(result["only_in_right"]) == 0
            assert len(result["modified"]) == 0
            assert len(result["same"]) == 1
    
    def test_compare_different_directories(self):
        """Test comparing directories with differences."""
        with tempfile.TemporaryDirectory() as dir1, \
             tempfile.TemporaryDirectory() as dir2:
            
            # Create different files
            with open(os.path.join(dir1, "file1.txt"), "w") as f:
                f.write("content1")
            with open(os.path.join(dir2, "file2.txt"), "w") as f:
                f.write("content2")
            
            result = compare_directories(dir1, dir2)
            
            assert len(result["only_in_left"]) == 1
            assert len(result["only_in_right"]) == 1


class TestEncodingDetection:
    """Test cases for encoding detection."""
    
    def test_read_file_with_encoding_detection_utf8(self):
        """Test encoding detection for UTF-8 files."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            temp_path = f.name
            f.write("hello world ü ö ä")
        
        try:
            content, encoding = read_file_with_encoding_detection(temp_path)
            assert content == "hello world ü ö ä"
            assert "utf-8" in encoding.lower()
        finally:
            os.unlink(temp_path)
    
    def test_read_file_with_encoding_detection_latin1(self):
        """Test encoding detection for Latin-1 files."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
            temp_path = f.name
            f.write(b"hello world \xe4\xf6\xfc")  # German umlauts in Latin-1
        
        try:
            content, encoding = read_file_with_encoding_detection(temp_path)
            assert "hello world" in content
        finally:
            os.unlink(temp_path)


class TestWriteFileWithEncoding:
    """Test cases for write_file_with_encoding."""
    
    def test_write_file_with_backup(self):
        """Test writing file with backup creation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
            f.write("original content")
        
        try:
            status, backup_path = write_file_with_encoding(
                temp_path, "new content", 
                should_backup=True
            )
            
            assert status == "success"
            assert backup_path is not None
            assert os.path.exists(backup_path)
            
            # Verify original file has new content
            content = read_file(temp_path)
            assert content == "new content"
            
            # Verify backup has original content
            backup_content = read_file(backup_path)
            assert backup_content == "original content"
            
            os.unlink(backup_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_write_file_without_backup(self):
        """Test writing file without backup."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
            f.write("original content")
        
        try:
            status, backup_path = write_file_with_encoding(
                temp_path, "new content",
                should_backup=False
            )
            
            assert status == "success"
            assert backup_path is None
            
            content = read_file(temp_path)
            assert content == "new content"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestMergeFiles:
    """Test cases for merge_files function."""
    
    def test_merge_identical_files(self):
        """Test merging identical files."""
        left = "line1\nline2\nline3"
        right = "line1\nline2\nline3"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            output_path = f.name
        
        try:
            from src.diff_engine import DiffEngine
            
            diff_result = DiffEngine.compare_text(left, right)
            result = merge_files(left, right, diff_result, output_path)
            
            assert result.success
            merged_content = read_file(output_path)
            assert merged_content == left
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_merge_with_insertions(self):
        """Test merging files with insertions."""
        left = "line1\nline2"
        right = "line1\nline2\nline3\nline4"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            output_path = f.name
        
        try:
            from src.diff_engine import DiffEngine
            
            diff_result = DiffEngine.compare_text(left, right)
            result = merge_files(left, right, diff_result, output_path)
            
            assert result.success
            merged_content = read_file(output_path)
            assert merged_content == right
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_merge_with_deletions(self):
        """Test merging files with deletions."""
        left = "line1\nline2\nline3\nline4"
        right = "line1\nline2"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            output_path = f.name
        
        try:
            from src.diff_engine import DiffEngine
            
            diff_result = DiffEngine.compare_text(left, right)
            result = merge_files(left, right, diff_result, output_path)
            
            assert result.success
            merged_content = read_file(output_path)
            # Deleted lines should be omitted
            assert merged_content == right
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestUndoRedoManager:
    """Test cases for UndoRedoManager."""
    
    def test_snapshot_and_undo(self):
        """Test taking snapshots and undoing."""
        manager = UndoRedoManager()
        
        # Take initial snapshot
        manager.snapshot("edit", "content1", "content2", "First edit")
        assert manager.can_undo()
        assert not manager.can_redo()
        
        # Take second snapshot
        manager.snapshot("edit", "content1a", "content2a", "Second edit")
        assert manager.get_undo_description() == "Second edit"
        
        # Undo
        restored = manager.undo()
        assert restored is not None
        assert manager.can_redo()
        assert manager.get_redo_description() == "Second edit"
    
    def test_redo(self):
        """Test redoing undone actions."""
        manager = UndoRedoManager()
        
        manager.snapshot("edit", "v1", "v1", "Version 1")
        manager.snapshot("edit", "v2", "v2", "Version 2")
        
        # Undo twice
        manager.undo()
        manager.undo()
        
        assert not manager.can_undo()
        assert manager.can_redo()
        
        # Redo - should restore Version 1
        restored = manager.redo()
        assert restored is not None
        assert restored.get("description") == "Version 1"
        assert manager.get_undo_description() == "Version 1"
        
        # Redo again - should restore Version 2
        restored = manager.redo()
        assert restored is not None
        assert restored.get("description") == "Version 2"
        assert manager.get_undo_description() == "Version 2"
    
    def test_clear(self):
        """Test clearing history."""
        manager = UndoRedoManager()
        
        manager.snapshot("edit", "c1", "c1", "Edit 1")
        manager.snapshot("edit", "c2", "c2", "Edit 2")
        
        assert manager.can_undo()
        
        manager.clear()
        
        assert not manager.can_undo()
        assert not manager.can_redo()
    
    def test_max_history(self):
        """Test that history is limited."""
        manager = UndoRedoManager(max_history=3)
        
        for i in range(5):
            manager.snapshot("edit", f"v{i}", f"v{i}", f"Version {i}")
        
        undo_count, _ = manager.get_history_count()
        assert undo_count == 3  # Should be limited to max_history
