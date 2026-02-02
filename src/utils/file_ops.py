"""
File operations utilities.
"""

import os
import shutil
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
import codecs


# Common encodings to try in order of likelihood
COMMON_ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "gbk", "shift_jis", "euc-kr"]


def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """Read a file and return its contents."""
    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        return f.read()


def read_file_with_encoding_detection(file_path: str) -> Tuple[str, str]:
    """Read a file with automatic encoding detection.
    
    Returns:
        Tuple of (content, detected_encoding)
    """
    # First try UTF-8 with BOM
    for enc in ["utf-8-sig", "utf-8"]:
        try:
            with open(file_path, "r", encoding=enc, errors="strict") as f:
                content = f.read()
            return content, enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    # Try common encodings
    for enc in COMMON_ENCODINGS:
        if enc in ["utf-8", "utf-8-sig"]:
            continue  # Already tried
        try:
            with open(file_path, "r", encoding=enc, errors="strict") as f:
                content = f.read()
            return content, enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    # Fallback to UTF-8 with replacement
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    return content, "utf-8 (with replacements)"


def write_file(file_path: str, content: str, encoding: str = "utf-8") -> None:
    """Write content to a file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)


def write_file_with_encoding(
    file_path: str, 
    content: str, 
    encoding: str = "utf-8",
    should_backup: bool = False,
    backup_dir: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    """Write content to a file with optional backup.
    
    Args:
        file_path: Path to write to
        content: Content to write
        encoding: Encoding to use
        should_backup: Whether to create a backup first
        backup_dir: Directory for backups
        
    Returns:
        Tuple of (status, backup_path if created)
    """
    backup_path = None
    
    if should_backup and os.path.exists(file_path):
        backup_path = create_backup(file_path, backup_dir)
    
    write_file(file_path, content, encoding)
    
    return "success", backup_path


def create_backup(file_path: str, backup_dir: Optional[str] = None) -> str:
    """Create a backup of the file."""
    if not os.path.exists(file_path):
        raise ValueError(f"File does not exist: {file_path}")
    
    if backup_dir is None:
        backup_dir = os.path.join(os.path.dirname(file_path), "backups")
    
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename with timestamp
    base_name = os.path.basename(file_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{base_name}.{timestamp}.bak"
    backup_path = os.path.join(backup_dir, backup_name)
    
    shutil.copy2(file_path, backup_path)
    return backup_path


def get_file_info(file_path: str) -> dict:
    """Get information about a file."""
    info = {
        "path": file_path,
        "name": os.path.basename(file_path),
        "size": 0,
        "modified": None,
        "is_file": os.path.isfile(file_path),
        "is_dir": os.path.isdir(file_path),
        "encoding": None,
    }
    
    if os.path.exists(file_path):
        stat = os.stat(file_path)
        info["size"] = stat.st_mtime
        info["modified"] = datetime.fromtimestamp(stat.st_mtime)
        if os.path.isfile(file_path):
            info["size"] = stat.st_size
            _, info["encoding"] = read_file_with_encoding_detection(file_path)
    
    return info


def compare_directories(dir1: str, dir2: str) -> dict:
    """Compare two directories and return differences."""
    results = {
        "only_in_left": [],
        "only_in_right": [],
        "modified": [],
        "same": [],
    }
    
    if not os.path.isdir(dir1) or not os.path.isdir(dir2):
        return results
    
    # Get all files and directories
    left_items = set(os.listdir(dir1))
    right_items = set(os.listdir(dir2))
    
    # Find differences
    for item in left_items:
        left_path = os.path.join(dir1, item)
        right_path = os.path.join(dir2, item)
        
        if item not in right_items:
            results["only_in_left"].append(left_path)
        elif os.path.isfile(left_path) and os.path.isfile(right_path):
            # Compare file contents
            if read_file(left_path) != read_file(right_path):
                results["modified"].append((left_path, right_path))
            else:
                results["same"].append(left_path)
        else:
            results["same"].append(left_path)
    
    for item in right_items:
        if item not in left_items:
            results["only_in_right"].append(os.path.join(dir2, item))
    
    return results


class MergeResult:
    """Result of a merge operation."""
    
    def __init__(
        self, 
        success: bool, 
        output_path: Optional[str] = None,
        backup_path: Optional[str] = None,
        error: Optional[str] = None
    ):
        self.success = success
        self.output_path = output_path
        self.backup_path = backup_path
        self.error = error
    
    def __repr__(self) -> str:
        if self.success:
            return f"MergeResult(success=True, output={self.output_path})"
        return f"MergeResult(success=False, error={self.error})"


def merge_files(
    left_content: str,
    right_content: str,
    diff_result: "DiffResult",
    output_path: str,
    encoding: str = "utf-8",
    create_backup_before_merge: bool = True
) -> MergeResult:
    """Merge two file contents based on diff result.
    
    This creates a merged file by taking:
    - Equal lines from left (or right, they're the same)
    - Insertions from right
    - Deletions are omitted
    - Replacements use right content
    
    Args:
        left_content: Content of the left file
        right_content: Content of the right file
        diff_result: Result of the diff operation
        output_path: Path to write the merged file
        encoding: Encoding to use for output
        create_backup_before_merge: Whether to backup existing file
        
    Returns:
        MergeResult indicating success or failure
    """
    from src.diff_engine import DiffType
    
    try:
        # Handle empty case
        if not diff_result or not diff_result.lines:
            if left_content == right_content:
                merged_content = left_content
            else:
                merged_content = right_content
        else:
            # Build merged content based on diff types
            merged_lines = []
            left_lines = left_content.split('\n') if left_content else []
            right_lines = right_content.split('\n') if right_content else []
            
            left_idx = 0
            right_idx = 0
            
            for diff_line in diff_result.lines:
                if diff_line.type == DiffType.EQUAL:
                    # Use left line (they should be equal)
                    if left_idx < len(left_lines):
                        merged_lines.append(left_lines[left_idx])
                        left_idx += 1
                        right_idx += 1
                elif diff_line.type == DiffType.INSERT:
                    # Use right line (new content)
                    if right_idx < len(right_lines):
                        merged_lines.append(right_lines[right_idx])
                        right_idx += 1
                elif diff_line.type == DiffType.DELETE:
                    # Skip (deleted from right)
                    left_idx += 1
                elif diff_line.type == DiffType.REPLACE:
                    # Use right line (replacement)
                    if right_idx < len(right_lines):
                        merged_lines.append(right_lines[right_idx])
                        right_idx += 1
                    left_idx += 1
            
            merged_content = '\n'.join(merged_lines)
        
        # Handle final line without newline
        if not merged_content.endswith('\n') and (left_content.endswith('\n') or right_content.endswith('\n')):
            merged_content += '\n'
        
        backup_path = None
        if create_backup_before_merge and os.path.exists(output_path):
            backup_path = create_backup(output_path)
        
        write_file(output_path, merged_content, encoding)
        
        return MergeResult(
            success=True,
            output_path=output_path,
            backup_path=backup_path
        )
        
    except Exception as e:
        return MergeResult(
            success=False,
            error=str(e)
        )


# For backward compatibility with imports
from src.diff_engine import DiffResult, DirectoryDiffResult


class UndoRedoManager:
    """Manager for undo/redo operations during merge editing.
    
    Stores snapshots of content at each significant edit point,
    allowing users to undo/redo merge changes.
    """
    
    def __init__(self, max_history: int = 50):
        """Initialize the undo/redo manager.
        
        Args:
            max_history: Maximum number of history entries to keep
        """
        self._undo_stack: List[Dict[str, Any]] = []
        self._redo_stack: List[Dict[str, Any]] = []
        self._max_history = max_history
    
    def snapshot(
        self, 
        action_type: str, 
        left_content: str, 
        right_content: str,
        description: str = ""
    ) -> None:
        """Save a snapshot of current state.
        
        Args:
            action_type: Type of action (e.g., 'copy_left', 'copy_right', 'edit')
            left_content: Current left pane content
            right_content: Current right pane content
            description: Human-readable description of the action
        """
        snapshot = {
            "action_type": action_type,
            "left_content": left_content,
            "right_content": right_content,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        
        self._undo_stack.append(snapshot)
        self._redo_stack.clear()  # Clear redo stack on new action
        
        # Trim history if needed
        if len(self._undo_stack) > self._max_history:
            self._undo_stack.pop(0)
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0
    
    def undo(self) -> Optional[Dict[str, Any]]:
        """Undo the last action.
        
        Returns:
            The snapshot being undone, or None if nothing to undo
        """
        if not self.can_undo():
            return None
        
        snapshot = self._undo_stack.pop()
        self._redo_stack.append(snapshot)
        
        # Return the state before the undo (second-to-last if exists)
        if self._undo_stack:
            return self._undo_stack[-1]
        return None
    
    def redo(self) -> Optional[Dict[str, Any]]:
        """Redo the last undone action.
        
        Returns:
            The snapshot being redone, or None if nothing to redo
        """
        if not self.can_redo():
            return None
        
        snapshot = self._redo_stack.pop()
        self._undo_stack.append(snapshot)
        return snapshot
    
    def get_undo_description(self) -> str:
        """Get description of the next action to undo."""
        if self._undo_stack:
            return self._undo_stack[-1].get("description", "Unknown action")
        return ""
    
    def get_redo_description(self) -> str:
        """Get description of the next action to redo."""
        if self._redo_stack:
            return self._redo_stack[-1].get("description", "Unknown action")
        return ""
    
    def clear(self) -> None:
        """Clear all history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
    
    def get_history_count(self) -> Tuple[int, int]:
        """Get the number of undo and redo entries."""
        return len(self._undo_stack), len(self._redo_stack)
