"""
Folder synchronization manager for bidirectional folder sync.

Provides functionality to synchronize two directories with conflict resolution.
"""

import logging
logger = logging.getLogger("MergeDiffTool.SyncManager")

import os
import shutil
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path


class SyncDirection(Enum):
    """Direction of synchronization."""
    LEFT_TO_RIGHT = "left_to_right"
    RIGHT_TO_LEFT = "right_to_left"
    BIDIRECTIONAL = "bidirectional"


class ConflictResolution(Enum):
    """Strategy for resolving sync conflicts."""
    SKIP = "skip"
    LEFT_WINS = "left_wins"
    RIGHT_WINS = "right_wins"
    NEWER_WINS = "newer_wins"
    LARGER_WINS = "larger_wins"
    PROMPT = "prompt"


@dataclass
class SyncConflict:
    """Represents a synchronization conflict."""
    path: str
    left_path: str
    right_path: str
    left_modified: datetime
    right_modified: datetime
    left_size: int
    right_size: int
    reason: str


@dataclass
class SyncOperation:
    """Represents a synchronization operation."""
    operation_type: str
    source_path: str
    destination_path: str
    is_directory: bool = False
    size: int = 0


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    success: bool
    operations_performed: List[SyncOperation] = field(default_factory=list)
    conflicts: List[SyncConflict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    files_copied: int = 0
    directories_created: int = 0
    bytes_transferred: int = 0


class SyncManager:
    """Manager for folder synchronization operations."""

    def __init__(self):
        """Initialize the sync manager."""
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None
        self._conflict_callback: Optional[Callable[[SyncConflict], ConflictResolution]] = None

    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Set a callback for progress updates.
        
        Args:
            callback: Function called with (current, total, message)
        """
        self._progress_callback = callback

    def set_conflict_callback(self, callback: Callable[[SyncConflict], ConflictResolution]):
        """Set a callback for conflict resolution.
        
        Args:
            callback: Function called with SyncConflict, returns ConflictResolution
        """
        self._conflict_callback = callback

    def preview_sync(
        self,
        left_path: str,
        right_path: str,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        ignore_patterns: Optional[List[str]] = None
    ) -> Tuple[List[SyncOperation], List[SyncConflict]]:
        """Preview synchronization operations without executing them.
        
        Args:
            left_path: Path to the left directory
            right_path: Path to the right directory
            direction: Direction of synchronization
            ignore_patterns: List of glob patterns to ignore
            
        Returns:
            Tuple of (operations, conflicts)
        """
        if not os.path.isdir(left_path):
            raise ValueError(f"Left path is not a directory: {left_path}")
        if not os.path.isdir(right_path):
            raise ValueError(f"Right path is not a directory: {right_path}")

        operations = []
        conflicts = []

        left_files = self._scan_directory(left_path, ignore_patterns)
        right_files = self._scan_directory(right_path, ignore_patterns)

        all_paths = set(left_files.keys()) | set(right_files.keys())

        for rel_path in sorted(all_paths):
            left_info = left_files.get(rel_path)
            right_info = right_files.get(rel_path)

            if direction in (SyncDirection.LEFT_TO_RIGHT, SyncDirection.BIDIRECTIONAL):
                if left_info and not right_info:
                    operations.append(SyncOperation(
                        operation_type="copy",
                        source_path=os.path.join(left_path, rel_path),
                        destination_path=os.path.join(right_path, rel_path),
                        is_directory=left_info["is_dir"],
                        size=left_info["size"]
                    ))

            if direction in (SyncDirection.RIGHT_TO_LEFT, SyncDirection.BIDIRECTIONAL):
                if right_info and not left_info:
                    operations.append(SyncOperation(
                        operation_type="copy",
                        source_path=os.path.join(right_path, rel_path),
                        destination_path=os.path.join(left_path, rel_path),
                        is_directory=right_info["is_dir"],
                        size=right_info["size"]
                    ))

            if left_info and right_info:
                if left_info["is_dir"] != right_info["is_dir"]:
                    conflicts.append(SyncConflict(
                        path=rel_path,
                        left_path=os.path.join(left_path, rel_path),
                        right_path=os.path.join(right_path, rel_path),
                        left_modified=left_info["modified"],
                        right_modified=right_info["modified"],
                        left_size=left_info["size"],
                        right_size=right_info["size"],
                        reason="Type mismatch (file vs directory)"
                    ))
                elif not left_info["is_dir"]:
                    if left_info["hash"] != right_info["hash"]:
                        if direction == SyncDirection.LEFT_TO_RIGHT:
                            operations.append(SyncOperation(
                                operation_type="copy",
                                source_path=os.path.join(left_path, rel_path),
                                destination_path=os.path.join(right_path, rel_path),
                                is_directory=False,
                                size=left_info["size"]
                            ))
                        elif direction == SyncDirection.RIGHT_TO_LEFT:
                            operations.append(SyncOperation(
                                operation_type="copy",
                                source_path=os.path.join(right_path, rel_path),
                                destination_path=os.path.join(left_path, rel_path),
                                is_directory=False,
                                size=right_info["size"]
                            ))
                        else:
                            conflicts.append(SyncConflict(
                                path=rel_path,
                                left_path=os.path.join(left_path, rel_path),
                                right_path=os.path.join(right_path, rel_path),
                                left_modified=left_info["modified"],
                                right_modified=right_info["modified"],
                                left_size=left_info["size"],
                                right_size=right_info["size"],
                                reason="Content differs"
                            ))

        return operations, conflicts

    def sync_folders(
        self,
        left_path: str,
        right_path: str,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        ignore_patterns: Optional[List[str]] = None,
        conflict_resolution: ConflictResolution = ConflictResolution.PROMPT
    ) -> SyncResult:
        """Synchronize two directories.
        
        Args:
            left_path: Path to the left directory
            right_path: Path to the right directory
            direction: Direction of synchronization
            ignore_patterns: List of glob patterns to ignore
            conflict_resolution: Strategy for resolving conflicts
            
        Returns:
            SyncResult with details of the operation
        """
        result = SyncResult(success=True)

        try:
            operations, conflicts = self.preview_sync(
                left_path, right_path, direction, ignore_patterns
            )

            result.conflicts = conflicts

            total_operations = len(operations)
            for i, operation in enumerate(operations):
                if self._progress_callback:
                    self._progress_callback(i + 1, total_operations, operation.source_path)

                try:
                    if operation.operation_type == "copy":
                        self._copy_item(
                            operation.source_path,
                            operation.destination_path,
                            operation.is_directory
                        )
                        result.operations_performed.append(operation)

                        if operation.is_directory:
                            result.directories_created += 1
                        else:
                            result.files_copied += 1
                            result.bytes_transferred += operation.size

                except Exception as e:
                    error_msg = f"Failed to copy {operation.source_path}: {e}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)

            for conflict in conflicts:
                resolution = self._resolve_conflict(conflict, conflict_resolution)
                if resolution == ConflictResolution.SKIP:
                    continue
                elif resolution == ConflictResolution.LEFT_WINS:
                    self._copy_item(conflict.left_path, conflict.right_path, False)
                    result.files_copied += 1
                elif resolution == ConflictResolution.RIGHT_WINS:
                    self._copy_item(conflict.right_path, conflict.left_path, False)
                    result.files_copied += 1

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"Sync failed: {e}")

        return result

    def _scan_directory(
        self,
        path: str,
        ignore_patterns: Optional[List[str]] = None
    ) -> Dict[str, dict]:
        """Scan a directory and return file information.
        
        Args:
            path: Directory path to scan
            ignore_patterns: List of glob patterns to ignore
            
        Returns:
            Dictionary mapping relative paths to file info
        """
        import fnmatch

        files = {}
        ignore_patterns = ignore_patterns or []

        for root, dirs, filenames in os.walk(path):
            root_path = Path(root)
            rel_root = root_path.relative_to(path)

            for dirname in dirs[:]:
                rel_dir = rel_root / dirname
                if any(fnmatch.fnmatch(str(rel_dir), pattern) for pattern in ignore_patterns):
                    dirs.remove(dirname)
                    continue

                files[str(rel_dir)] = {
                    "is_dir": True,
                    "size": 0,
                    "modified": datetime.fromtimestamp(os.path.getmtime(root / dirname)),
                    "hash": ""
                }

            for filename in filenames:
                rel_file = rel_root / filename
                if any(fnmatch.fnmatch(str(rel_file), pattern) for pattern in ignore_patterns):
                    continue

                full_path = root / filename
                stat = os.stat(full_path)
                files[str(rel_file)] = {
                    "is_dir": False,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "hash": self._compute_file_hash(full_path)
                }

        return files

    def _compute_file_hash(self, path: str) -> str:
        """Compute a hash of the file content."""
        import hashlib
        hash_obj = hashlib.md5()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            return ""

    def _copy_item(self, source: str, destination: str, is_directory: bool):
        """Copy a file or directory."""
        dest_dir = os.path.dirname(destination)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)

        if is_directory:
            if os.path.exists(destination):
                shutil.rmtree(destination)
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

    def _resolve_conflict(
        self,
        conflict: SyncConflict,
        default_resolution: ConflictResolution
    ) -> ConflictResolution:
        """Resolve a synchronization conflict."""
        if default_resolution != ConflictResolution.PROMPT:
            return default_resolution

        if self._conflict_callback:
            return self._conflict_callback(conflict)

        if default_resolution == ConflictResolution.NEWER_WINS:
            return ConflictResolution.LEFT_WINS if conflict.left_modified > conflict.right_modified else ConflictResolution.RIGHT_WINS
        elif default_resolution == ConflictResolution.LARGER_WINS:
            return ConflictResolution.LEFT_WINS if conflict.left_size > conflict.right_size else ConflictResolution.RIGHT_WINS

        return ConflictResolution.SKIP
