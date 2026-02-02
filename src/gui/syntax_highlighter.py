"""
Syntax highlighter for various programming languages.

Provides syntax highlighting for Python, JavaScript, Java, C++, HTML, CSS, JSON, XML, and more.
"""

import re
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from typing import List, Tuple, Dict


class SyntaxHighlighter(QSyntaxHighlighter):
    """Base syntax highlighter class."""

    def __init__(self, document, language: str = "python"):
        super().__init__(document)
        self.language = language.lower()
        self._setup_highlighting_rules()

    def _setup_highlighting_rules(self):
        """Set up highlighting rules based on language."""
        self.highlighting_rules = []

        if self.language == "python":
            self._setup_python_rules()
        elif self.language in ["javascript", "js", "typescript", "ts"]:
            self._setup_javascript_rules()
        elif self.language in ["java"]:
            self._setup_java_rules()
        elif self.language in ["c", "cpp", "cxx", "cc", "h", "hpp"]:
            self._setup_cpp_rules()
        elif self.language in ["html", "htm"]:
            self._setup_html_rules()
        elif self.language in ["css"]:
            self._setup_css_rules()
        elif self.language in ["json"]:
            self._setup_json_rules()
        elif self.language in ["xml"]:
            self._setup_xml_rules()
        elif self.language in ["sql"]:
            self._setup_sql_rules()
        elif self.language in ["bash", "sh", "shell"]:
            self._setup_shell_rules()
        else:
            self._setup_python_rules()

    def _create_format(self, color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        """Create a text format with specified properties."""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def _add_rule(self, pattern: str, format: QTextCharFormat):
        """Add a highlighting rule."""
        self.highlighting_rules.append((re.compile(pattern), format))

    def _setup_python_rules(self):
        """Set up Python syntax highlighting rules."""
        keyword_format = self._create_format("#0000FF", bold=True)
        string_format = self._create_format("#008000")
        comment_format = self._create_format("#808080", italic=True)
        number_format = self._create_format("#FF00FF")
        function_format = self._create_format("#800080", bold=True)
        decorator_format = self._create_format("#FF8000", bold=True)

        keywords = [
            r'\b(def|class|if|elif|else|for|while|try|except|finally|with|'
            r'import|from|as|return|yield|raise|pass|break|continue|'
            r'and|or|not|in|is|lambda|True|False|None|async|await|'
            r'global|nonlocal|assert|del|exec|print)\b'
        ]
        for keyword in keywords:
            self._add_rule(keyword, keyword_format)

        self._add_rule(r'@\w+', decorator_format)
        self._add_rule(r'\bdef\s+(\w+)', function_format)
        self._add_rule(r'\bclass\s+(\w+)', function_format)
        self._add_rule(r'""".*?"""', string_format)
        self._add_rule(r"'''.*?'''", string_format)
        self._add_rule(r'"(?:[^"\\]|\\.)*"', string_format)
        self._add_rule(r"'(?:[^'\\]|\\.)*'", string_format)
        self._add_rule(r'\b\d+\.?\d*\b', number_format)
        self._add_rule(r'#.*$', comment_format)

    def _setup_javascript_rules(self):
        """Set up JavaScript/TypeScript syntax highlighting rules."""
        keyword_format = self._create_format("#0000FF", bold=True)
        string_format = self._create_format("#008000")
        comment_format = self._create_format("#808080", italic=True)
        number_format = self._create_format("#FF00FF")
        function_format = self._create_format("#800080", bold=True)

        keywords = [
            r'\b(const|let|var|function|return|if|else|for|while|do|switch|'
            r'case|break|continue|try|catch|finally|throw|new|this|'
            r'class|extends|super|import|export|default|from|async|await|'
            r'yield|typeof|instanceof|in|of|delete|void|true|false|null|'
            r'undefined|NaN|Infinity)\b'
        ]
        for keyword in keywords:
            self._add_rule(keyword, keyword_format)

        self._add_rule(r'\bfunction\s+(\w+)', function_format)
        self._add_rule(r'\b(\w+)\s*\(', function_format)
        self._add_rule(r'//.*$', comment_format)
        self._add_rule(r'/\*.*?\*/', comment_format)
        self._add_rule(r'"(?:[^"\\]|\\.)*"', string_format)
        self._add_rule(r"'(?:[^'\\]|\\.)*'", string_format)
        self._add_rule(r'`(?:[^`\\]|\\.)*`', string_format)
        self._add_rule(r'\b\d+\.?\d*\b', number_format)

    def _setup_java_rules(self):
        """Set up Java syntax highlighting rules."""
        keyword_format = self._create_format("#0000FF", bold=True)
        string_format = self._create_format("#008000")
        comment_format = self._create_format("#808080", italic=True)
        number_format = self._create_format("#FF00FF")
        function_format = self._create_format("#800080", bold=True)
        annotation_format = self._create_format("#FF8000", bold=True)

        keywords = [
            r'\b(abstract|assert|boolean|break|byte|case|catch|char|class|'
            r'const|continue|default|do|double|else|enum|extends|final|'
            r'finally|float|for|goto|if|implements|import|instanceof|'
            r'int|interface|long|native|new|package|private|protected|'
            r'public|return|short|static|strictfp|super|switch|'
            r'synchronized|this|throw|throws|transient|try|void|'
            r'volatile|while|true|false|null)\b'
        ]
        for keyword in keywords:
            self._add_rule(keyword, keyword_format)

        self._add_rule(r'@\w+', annotation_format)
        self._add_rule(r'\b(\w+)\s*\(', function_format)
        self._add_rule(r'//.*$', comment_format)
        self._add_rule(r'/\*.*?\*/', comment_format)
        self._add_rule(r'"(?:[^"\\]|\\.)*"', string_format)
        self._add_rule(r'\b\d+\.?\d*[fFdDlL]?\b', number_format)

    def _setup_cpp_rules(self):
        """Set up C/C++ syntax highlighting rules."""
        keyword_format = self._create_format("#0000FF", bold=True)
        string_format = self._create_format("#008000")
        comment_format = self._create_format("#808080", italic=True)
        number_format = self._create_format("#FF00FF")
        function_format = self._create_format("#800080", bold=True)
        preprocessor_format = self._create_format("#FF8000", bold=True)

        keywords = [
            r'\b(auto|break|case|char|const|continue|default|do|double|'
            r'else|enum|extern|float|for|goto|if|int|long|register|'
            r'return|short|signed|sizeof|static|struct|switch|'
            r'typedef|union|unsigned|void|volatile|while|'
            r'class|private|public|protected|virtual|override|'
            r'final|constexpr|nullptr|decltype|template|typename|'
            r'true|false)\b'
        ]
        for keyword in keywords:
            self._add_rule(keyword, keyword_format)

        self._add_rule(r'#\s*\w+', preprocessor_format)
        self._add_rule(r'\b(\w+)\s*\(', function_format)
        self._add_rule(r'//.*$', comment_format)
        self._add_rule(r'/\*.*?\*/', comment_format)
        self._add_rule(r'"(?:[^"\\]|\\.)*"', string_format)
        self._add_rule(r'\b\d+\.?\d*[fFlLuU]?\b', number_format)

    def _setup_html_rules(self):
        """Set up HTML syntax highlighting rules."""
        tag_format = self._create_format("#0000FF", bold=True)
        attribute_format = self._create_format("#FF00FF")
        string_format = self._create_format("#008000")
        comment_format = self._create_format("#808080", italic=True)

        self._add_rule(r'<\s*/?\s*\w+', tag_format)
        self._add_rule(r'\s+\w+\s*=', attribute_format)
        self._add_rule(r'<!--.*?-->', comment_format)
        self._add_rule(r'"(?:[^"\\]|\\.)*"', string_format)
        self._add_rule(r"'(?:[^'\\]|\\.)*'", string_format)

    def _setup_css_rules(self):
        """Set up CSS syntax highlighting rules."""
        selector_format = self._create_format("#800080", bold=True)
        property_format = self._create_format("#FF00FF")
        value_format = self._create_format("#008000")
        comment_format = self._create_format("#808080", italic=True)

        self._add_rule(r'[.#]?\w+', selector_format)
        self._add_rule(r'\w+\s*:', property_format)
        self._add_rule(r':\s*[^;{]+', value_format)
        self._add_rule(r'/\*.*?\*/', comment_format)

    def _setup_json_rules(self):
        """Set up JSON syntax highlighting rules."""
        key_format = self._create_format("#800080", bold=True)
        string_format = self._create_format("#008000")
        number_format = self._create_format("#FF00FF")
        boolean_format = self._create_format("#0000FF", bold=True)
        null_format = self._create_format("#808080", italic=True)

        self._add_rule(r'"(?:[^"\\]|\\.)*"\s*:', key_format)
        self._add_rule(r'"(?:[^"\\]|\\.)*"', string_format)
        self._add_rule(r'\b\d+\.?\d*\b', number_format)
        self._add_rule(r'\b(true|false)\b', boolean_format)
        self._add_rule(r'\bnull\b', null_format)

    def _setup_xml_rules(self):
        """Set up XML syntax highlighting rules."""
        tag_format = self._create_format("#0000FF", bold=True)
        attribute_format = self._create_format("#FF00FF")
        string_format = self._create_format("#008000")
        comment_format = self._create_format("#808080", italic=True)

        self._add_rule(r'<\s*/?\s*[\w:]+', tag_format)
        self._add_rule(r'\s+[\w:]+\s*=', attribute_format)
        self._add_rule(r'<!--.*?-->', comment_format)
        self._add_rule(r'<!\[CDATA\[.*?\]\]>', string_format)
        self._add_rule(r'"(?:[^"\\]|\\.)*"', string_format)
        self._add_rule(r"'(?:[^'\\]|\\.)*'", string_format)

    def _setup_sql_rules(self):
        """Set up SQL syntax highlighting rules."""
        keyword_format = self._create_format("#0000FF", bold=True)
        string_format = self._create_format("#008000")
        comment_format = self._create_format("#808080", italic=True)
        number_format = self._create_format("#FF00FF")
        function_format = self._create_format("#800080", bold=True)

        keywords = [
            r'\b(SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|'
            r'DELETE|CREATE|TABLE|DROP|ALTER|INDEX|JOIN|LEFT|RIGHT|'
            r'INNER|OUTER|ON|AND|OR|NOT|IN|EXISTS|BETWEEN|LIKE|'
            r'ORDER BY|GROUP BY|HAVING|LIMIT|OFFSET|UNION|ALL|DISTINCT|'
            r'COUNT|SUM|AVG|MIN|MAX|AS|ASC|DESC|NULL|IS|TRUE|FALSE)\b'
        ]
        for keyword in keywords:
            self._add_rule(keyword, keyword_format)

        self._add_rule(r'\b(\w+)\s*\(', function_format)
        self._add_rule(r'--.*$', comment_format)
        self._add_rule(r'/\*.*?\*/', comment_format)
        self._add_rule(r"'(?:[^'\\]|\\.)*'", string_format)
        self._add_rule(r'\b\d+\.?\d*\b', number_format)

    def _setup_shell_rules(self):
        """Set up Shell/Bash syntax highlighting rules."""
        keyword_format = self._create_format("#0000FF", bold=True)
        string_format = self._create_format("#008000")
        comment_format = self._create_format("#808080", italic=True)
        variable_format = self._create_format("#FF00FF", bold=True)

        keywords = [
            r'\b(if|then|else|elif|fi|for|while|do|done|case|esac|'
            r'function|return|local|export|readonly|declare|'
            r'true|false|break|continue|exit|shift)\b'
        ]
        for keyword in keywords:
            self._add_rule(keyword, keyword_format)

        self._add_rule(r'\$\w+', variable_format)
        self._add_rule(r'\$\{[^}]+\}', variable_format)
        self._add_rule(r'#.*$', comment_format)
        self._add_rule(r'"(?:[^"\\]|\\.)*"', string_format)
        self._add_rule(r"'(?:[^'\\]|\\.)*'", string_format)

    def highlightBlock(self, text: str):
        """Highlight a block of text."""
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)


def detect_language_from_filename(filename: str) -> str:
    """Detect programming language from file extension."""
    if not filename:
        return "python"
    
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    language_map = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp',
        'cxx': 'cpp',
        'cc': 'cpp',
        'h': 'cpp',
        'hpp': 'cpp',
        'html': 'html',
        'htm': 'html',
        'css': 'css',
        'json': 'json',
        'xml': 'xml',
        'sql': 'sql',
        'sh': 'shell',
        'bash': 'shell',
    }
    
    return language_map.get(ext, 'python')