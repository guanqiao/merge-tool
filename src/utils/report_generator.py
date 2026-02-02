"""
Report generator for diff comparisons.

Generates HTML, Text, and JSON reports from diff results.
"""

import json
from typing import List, Optional
from datetime import datetime
from src.diff_engine import DiffResult, DiffType


class ReportGenerator:
    """Generator for various report formats."""

    @staticmethod
    def generate_html_report(diff_result: DiffResult, 
                          left_path: str = "", 
                          right_path: str = "",
                          left_content: str = "",
                          right_content: str = "") -> str:
        """Generate an HTML report of the diff."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        left_display = left_path or "N/A"
        right_display = right_path or "N/A"
        
        html_lines = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'    <title>Diff Report - {timestamp}</title>',
            '    <style>',
            '        body {',
            '            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;',
            '            margin: 0;',
            '            padding: 20px;',
            '            background-color: #f5f5f5;',
            '        }',
            '        .container {',
            '            max-width: 1400px;',
            '            margin: 0 auto;',
            '            background-color: white;',
            '            padding: 20px;',
            '            border-radius: 8px;',
            '            box-shadow: 0 2px 4px rgba(0,0,0,0.1);',
            '        }',
            '        .header {',
            '            border-bottom: 2px solid #007acc;',
            '            padding-bottom: 10px;',
            '            margin-bottom: 20px;',
            '        }',
            '        .header h1 {',
            '            margin: 0;',
            '            color: #007acc;',
            '        }',
            '        .info {',
            '            margin: 10px 0;',
            '            color: #666;',
            '            font-size: 14px;',
            '        }',
            '        .stats {',
            '            background-color: #f0f0f0;',
            '            padding: 15px;',
            '            border-radius: 4px;',
            '            margin-bottom: 20px;',
            '        }',
            '        .stats table {',
            '            width: 100%;',
            '            border-collapse: collapse;',
            '        }',
            '        .stats td {',
            '            padding: 8px;',
            '            border-bottom: 1px solid #ddd;',
            '        }',
            '        .diff-container {',
            '            display: flex;',
            '            gap: 20px;',
            '        }',
            '        .pane {',
            '            flex: 1;',
            '            border: 1px solid #ddd;',
            '            border-radius: 4px;',
            '            overflow: hidden;',
            '        }',
            '        .pane-header {',
            '            background-color: #007acc;',
            '            color: white;',
            '            padding: 10px;',
            '            font-weight: bold;',
            '        }',
            '        .diff-line {',
            '            display: flex;',
            '            padding: 2px 5px;',
            '            font-family: "Consolas", "Monaco", monospace;',
            '            font-size: 13px;',
            '            border-bottom: 1px solid #eee;',
            '        }',
            '        .diff-line:hover {',
            '            background-color: #f5f5f5;',
            '        }',
            '        .line-number {',
            '            width: 50px;',
            '            text-align: right;',
            '            padding-right: 10px;',
            '            color: #999;',
            '            flex-shrink: 0;',
            '        }',
            '        .line-content {',
            '            flex: 1;',
            '            white-space: pre-wrap;',
            '            word-break: break-all;',
            '        }',
            '        .equal {',
            '            background-color: white;',
            '        }',
            '        .insert {',
            '            background-color: #e6ffed;',
            '        }',
            '        .delete {',
            '            background-color: #ffeef0;',
            '        }',
            '        .replace {',
            '            background-color: #fff5b1;',
            '        }',
            '        .empty {',
            '            background-color: #f9f9f9;',
            '            color: #ccc;',
            '        }',
            '    </style>',
            '</head>',
            '<body>',
            '    <div class="container">',
            '        <div class="header">',
            '            <h1>Diff Report</h1>',
            '        </div>',
            '        ',
            f'        <div class="info">\n',
            f'            <strong>Generated:</strong> {timestamp}<br>\n',
            f'            <strong>Left File:</strong> {left_display}<br>\n',
            f'            <strong>Right File:</strong> {right_display}\n',
            '        </div>',
            '        ',
            '        <div class="stats">',
            '            <table>',
            f'                <tr>\n',
            f'                    <td><strong>Total Lines:</strong></td>\n',
            f'                    <td>{diff_result.left_line_count} (left) / {diff_result.right_line_count} (right)</td>\n',
            '                </tr>',
            f'                <tr>\n',
            f'                    <td><strong>Changes:</strong></td>\n',
            f'                    <td>{diff_result.change_count}</td>\n',
            '                </tr>',
            '            </table>',
            '        </div>',
            '        ',
            '        <div class="diff-container">',
            '            <div class="pane">',
            '                <div class="pane-header">Left</div>',
            '                <div class="diff-content">'
        ]
        
        for i, line in enumerate(diff_result.lines):
            line_class = line.type.value
            left_num = line.left_line_num or ""
            content = line.content if line.type != DiffType.INSERT else ""
            
            if not content and line.type == DiffType.INSERT:
                html_lines.append('                    <div class="diff-line empty"><span class="line-number"></span><span class="line-content">&nbsp;</span></div>')
            else:
                escaped_content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_lines.append(f'                    <div class="diff-line {line_class}"><span class="line-number">{left_num}</span><span class="line-content">{escaped_content}</span></div>')
        
        html_lines.extend([
            '                </div>',
            '            </div>',
            '            <div class="pane">',
            '                <div class="pane-header">Right</div>',
            '                <div class="diff-content">'
        ])
        
        for i, line in enumerate(diff_result.lines):
            line_class = line.type.value
            right_num = line.right_line_num or ""
            content = line.content if line.type != DiffType.DELETE else ""
            
            if not content and line.type == DiffType.DELETE:
                html_lines.append('                    <div class="diff-line empty"><span class="line-number"></span><span class="line-content">&nbsp;</span></div>')
            else:
                escaped_content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_lines.append(f'                    <div class="diff-line {line_class}"><span class="line-number">{right_num}</span><span class="line-content">{escaped_content}</span></div>')
        
        html_lines.extend([
            '                </div>',
            '            </div>',
            '        </div>',
            '    </div>',
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_lines)

    @staticmethod
    def generate_text_report(diff_result: DiffResult,
                          left_path: str = "",
                          right_path: str = "") -> str:
        """Generate a text report of the diff."""
        lines = []
        lines.append("=" * 80)
        lines.append("DIFF REPORT")
        lines.append("=" * 80)
        lines.append(f"Left File:  {left_path or 'N/A'}")
        lines.append(f"Right File: {right_path or 'N/A'}")
        lines.append(f"Generated:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("-" * 80)
        lines.append(f"Total Lines: {diff_result.left_line_count} (left) / {diff_result.right_line_count} (right)")
        lines.append(f"Changes:     {diff_result.change_count}")
        lines.append("-" * 80)
        lines.append("")
        
        for line in diff_result.lines:
            prefix = "  "
            if line.type == DiffType.INSERT:
                prefix = "+ "
            elif line.type == DiffType.DELETE:
                prefix = "- "
            elif line.type == DiffType.REPLACE:
                prefix = "~ "
            
            left_num = f"{line.left_line_num:4d}" if line.left_line_num else "    "
            right_num = f"{line.right_line_num:4d}" if line.right_line_num else "    "
            
            lines.append(f"{left_num} {right_num} {prefix} {line.content}")
        
        return "\n".join(lines)

    @staticmethod
    def generate_unified_diff_report(diff_result: DiffResult,
                                   left_path: str = "",
                                   right_path: str = "",
                                   left_content: str = "",
                                   right_content: str = "") -> str:
        """Generate a unified diff format report."""
        lines = []
        lines.append(f"--- {left_path or 'left'}")
        lines.append(f"+++ {right_path or 'right'}")
        lines.append(f"@@ -1,{diff_result.left_line_count} +1,{diff_result.right_line_count} @@")
        
        for line in diff_result.lines:
            prefix = "  "
            if line.type == DiffType.INSERT:
                prefix = "+"
            elif line.type == DiffType.DELETE:
                prefix = "-"
            elif line.type == DiffType.REPLACE:
                prefix = "-"
            
            lines.append(f"{prefix}{line.content}")
        
        return "\n".join(lines)

    @staticmethod
    def generate_json_report(diff_result: DiffResult,
                          left_path: str = "",
                          right_path: str = "",
                          left_content: str = "",
                          right_content: str = "") -> str:
        """Generate a JSON report of the diff."""
        report = {
            "metadata": {
                "generated": datetime.now().isoformat(),
                "left_file": left_path,
                "right_file": right_path,
                "left_line_count": diff_result.left_line_count,
                "right_line_count": diff_result.right_line_count,
                "change_count": diff_result.change_count
            },
            "differences": []
        }
        
        for i, line in enumerate(diff_result.lines):
            if line.type != DiffType.EQUAL:
                diff_entry = {
                    "line_number": i + 1,
                    "type": line.type.value,
                    "content": line.content,
                    "left_line_number": line.left_line_num,
                    "right_line_number": line.right_line_num
                }
                report["differences"].append(diff_entry)
        
        return json.dumps(report, indent=2, ensure_ascii=False)

    @staticmethod
    def save_report(content: str, file_path: str) -> bool:
        """Save report content to a file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving report: {e}")
            return False