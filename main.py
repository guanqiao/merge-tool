"""Main entry point for the Merge & Diff Tool."""

import sys
import os
import argparse
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('merge_tool.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("MergeDiffTool")


def print_diff_result(result, output_format="text"):
    """Print diff result to console."""
    if output_format == "text":
        for line in result.lines:
            if line.type.value == "equal":
                print(f"  {line.content}")
            elif line.type.value == "insert":
                print(f"+ {line.content}")
            elif line.type.value == "delete":
                print(f"- {line.content}")
            elif line.type.value == "replace":
                print(f"? {line.content}")
    elif output_format == "unified":
        unified_lines = []
        for line in result.lines:
            if line.type.value == "equal":
                unified_lines.append(f"  {line.content}")
            elif line.type.value == "insert":
                unified_lines.append(f"+ {line.content}")
            elif line.type.value == "delete":
                unified_lines.append(f"- {line.content}")
            elif line.type.value == "replace":
                unified_lines.append(f"- {line.content}")
                unified_lines.append(f"+ {line.content}")
        print('\n'.join(unified_lines))
    elif output_format == "json":
        import json
        data = {
            "left_line_count": result.left_line_count,
            "right_line_count": result.right_line_count,
            "change_count": result.change_count,
            "lines": [
                {
                    "type": line.type.value,
                    "content": line.content,
                    "is_change": line.is_change
                }
                for line in result.lines
            ]
        }
        print(json.dumps(data, indent=2))


def compare_files_cli(left_path: str, right_path: str, output_format: str = "text"):
    """Compare two files from command line."""
    try:
        from src.diff_engine import DiffEngine

        result = DiffEngine.compare_files(left_path, right_path)
        print(f"Comparing: {left_path} vs {right_path}")
        print(f"Left lines: {result.left_line_count}, Right lines: {result.right_line_count}")
        print(f"Changes: {result.change_count}")
        print("-" * 50)
        print_diff_result(result, output_format)
        return 0
    except Exception as e:
        print(f"Error comparing files: {e}", file=sys.stderr)
        return 1


def compare_text_cli(left_text: str, right_text: str, output_format: str = "text"):
    """Compare two text strings from command line."""
    try:
        from src.diff_engine import DiffEngine

        result = DiffEngine.compare_text(left_text, right_text)
        print(f"Changes: {result.change_count}")
        print("-" * 50)
        print_diff_result(result, output_format)
        return 0
    except Exception as e:
        print(f"Error comparing text: {e}", file=sys.stderr)
        return 1


def compare_directories_cli(left_path: str, right_path: str, recursive: bool = True):
    """Compare two directories from command line."""
    try:
        from src.diff_engine import DirectoryDiffEngine

        result = DirectoryDiffEngine.compare_directories(left_path, right_path)
        print(f"Comparing directories: {left_path} vs {right_path}")
        print(f"Total entries: {result.total_count}")
        print(f"Modified files: {result.modified_count}")
        print(f"Only in left: {result.only_left_count}")
        print(f"Only in right: {result.only_right_count}")
        print("-" * 50)

        for entry in result.entries:
            if entry.is_only_left:
                print(f"[LEFT ONLY] {entry.name}")
            elif entry.is_only_right:
                print(f"[RIGHT ONLY] {entry.name}")
            elif entry.is_modified:
                print(f"[MODIFIED] {entry.name}")
            else:
                print(f"[EQUAL] {entry.name}")

        return 0
    except Exception as e:
        print(f"Error comparing directories: {e}", file=sys.stderr)
        return 1


def generate_patch_cli(left_path: str, right_path: str, output_path: str = None):
    """Generate a patch file from two files."""
    try:
        from src.diff_engine import DiffEngine

        left_lines = []
        right_lines = []

        with open(left_path, "r", encoding="utf-8", errors="replace") as f:
            left_lines = f.read().splitlines(keepends=False)

        with open(right_path, "r", encoding="utf-8", errors="replace") as f:
            right_lines = f.read().splitlines(keepends=False)

        patch_lines = DiffEngine.get_unified_diff(
            left_lines, right_lines,
            fromfile=left_path,
            tofile=right_path
        )

        patch_content = '\n'.join(patch_lines)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(patch_content)
            print(f"Patch written to: {output_path}")
        else:
            print(patch_content)

        return 0
    except Exception as e:
        print(f"Error generating patch: {e}", file=sys.stderr)
        return 1


def create_arg_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Merge & Diff Tool - A WinMerge-like GUI tool for comparing and merging files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                  # Open GUI
  %(prog)s file1.txt file2.txt             # Compare two files
  %(prog)s dir1/ dir2/                     # Compare two directories
  %(prog)s -c file1.txt file2.txt          # Compare with colored output
  %(prog)s --patch file1.txt file2.txt > diff.patch
  %(prog)s --json file1.txt file2.txt      # Output in JSON format
        """
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 0.2.0"
    )

    parser.add_argument(
        "-c", "--color",
        action="store_true",
        help="Force colored output (for terminal)"
    )

    parser.add_argument(
        "--json",
        action="store_const",
        dest="output_format",
        const="json",
        default="text",
        help="Output in JSON format"
    )

    parser.add_argument(
        "--unified",
        action="store_const",
        dest="output_format",
        const="unified",
        default="text",
        help="Output in unified diff format"
    )

    parser.add_argument(
        "--patch",
        action="store_true",
        help="Generate patch file output"
    )

    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Output file path (for patch or JSON)"
    )

    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        default=True,
        help="Recursively compare directories (default)"
    )

    parser.add_argument(
        "left",
        nargs="?",
        metavar="LEFT",
        help="Left file or directory path"
    )

    parser.add_argument(
        "right",
        nargs="?",
        metavar="RIGHT",
        help="Right file or directory path"
    )

    return parser


def main():
    """Application entry point."""
    print("Starting Merge & Diff Tool...")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    logger.info("Starting Merge & Diff Tool...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")

    parser = create_arg_parser()
    args = parser.parse_args()

    if args.left is None or args.right is None:
        pass
    else:
        left_path = args.left
        right_path = args.right

        if args.patch:
            output_path = args.output
            sys.exit(generate_patch_cli(left_path, right_path, output_path))

        if args.output_format != "text":
            sys.exit(compare_files_cli(left_path, right_path, args.output_format))

        left_exists = os.path.exists(left_path)
        right_exists = os.path.exists(right_path)

        if not left_exists:
            print(f"Error: Left path does not exist: {left_path}", file=sys.stderr)
            sys.exit(1)
        if not right_exists:
            print(f"Error: Right path does not exist: {right_path}", file=sys.stderr)
            sys.exit(1)

        left_is_dir = os.path.isdir(left_path)
        right_is_dir = os.path.isdir(right_path)

        if left_is_dir and right_is_dir:
            sys.exit(compare_directories_cli(left_path, right_path, args.recursive))
        elif not left_is_dir and not right_is_dir:
            sys.exit(compare_files_cli(left_path, right_path))
        else:
            print("Error: Both paths must be files or both must be directories", file=sys.stderr)
            sys.exit(1)

    try:
        from PySide6.QtWidgets import QApplication
        logger.info("Successfully imported PySide6.QtWidgets")
    except ImportError as e:
        logger.error(f"Failed to import PySide6: {e}")
        sys.exit(1)

    logger.info("Creating QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("Merge & Diff Tool")
    app.setApplicationVersion("0.2.0")

    if args.color:
        app.setStyleSheet("")

    logger.info("QApplication created successfully")

    try:
        from src.gui.main_window import MainWindow
        logger.info("Successfully imported MainWindow")
    except ImportError as e:
        logger.error(f"Failed to import MainWindow: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

    logger.info("Creating MainWindow...")
    window = MainWindow()
    logger.info("MainWindow created successfully")

    if args.left and args.right:
        from src.gui.diff_view import DiffView
        if os.path.isfile(args.left) and os.path.isfile(args.right):
            window.diff_view.compare_files(args.left, args.right)

    logger.info("Showing window...")
    window.show()
    logger.info("Window show() called")

    app.processEvents()
    logger.info("Events processed")

    logger.info("Entering main event loop...")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
