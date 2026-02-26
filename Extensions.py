from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFileSystemModel
from PyQt6.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHeaderView, QLabel, QTreeView
from PyQt6.QtCore import Qt, pyqtSignal
import re
import json
import os
from pathlib import Path

class Highlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        BASE_DIR = Path(__file__).resolve().parent

# JSON is in the same folder as this script
        json_path = BASE_DIR / "Format.json"

        # Load formatting colors from JSON
        with open(json_path, "r") as f:
            self.rules_dict: dict = json.load(f)

        def make_format(color: str) -> QTextCharFormat:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            return fmt

        self.rules = []

        # --- Keywords ---
        keyword_format = make_format(self.rules_dict.get("keywords", "#FF8800"))
        pykeywords: list[str] = self.rules_dict.get("pykeywords", [])
        for kw in pykeywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            self.rules.append((re.compile(pattern), keyword_format))

        # --- Numbers ---
        number_format = make_format(self.rules_dict.get("number", "#E6A700"))
        number_pattern = re.compile(r"\b(\d+\.\d+([eE][+-]?\d+)?|\d+[eE][+-]?\d+|\d+)\b")
        self.rules.append((number_pattern, number_format))

        # --- Strings ---
        string_format = make_format(self.rules_dict.get("strings", "#2ECC71"))
        self.rules.append((re.compile(r'"""(.*?)"""', re.DOTALL), string_format))
        self.rules.append((re.compile(r"'''(.*?)'''", re.DOTALL), string_format))
        self.rules.append((re.compile(r'"(.*?)"'), string_format))
        self.rules.append((re.compile(r"'(.*?)'"), string_format))

        # --- Booleans & None ---
        bool_format = make_format(self.rules_dict.get("bool", "#FF5555"))
        self.rules.append((re.compile(r"\b(True|False|None)\b"), bool_format))

        # --- Function definitions ---
        func_format = make_format(self.rules_dict.get("function", "#C7C408"))
        self.rules.append((re.compile(r"\bdef\s+([A-Za-z_]\w*)"), func_format))
        # function calls
        self.rules.append((re.compile(r"\b([A-Za-z_]\w*)(?=\()"), func_format))

        # --- Class definitions ---
        class_format = make_format(self.rules_dict.get("class", "#56B6C2"))
        self.rules.append((re.compile(r"\bclass\s+([A-Za-z_]\w*)"), class_format))

        # --- Constants (ALL_CAPS) ---
        const_format = make_format(self.rules_dict.get("constants", "#1900FF"))
        self.rules.append((re.compile(r"\b[A-Z_][A-Z0-9_]*\b"), const_format))

        # --- Private / protected names (_prefix) ---
        private_format = make_format(self.rules_dict.get("private", "#C678DD"))
        self.rules.append((re.compile(r"\b_[A-Za-z_]\w*\b"), private_format))

        # --- Decorators (@) ---
        decorator_format = make_format(self.rules_dict.get("@", "#FF4FD8"))
        self.rules.append((re.compile(r"@\w+"), decorator_format))

        # --- Brackets ---
        parens_format = make_format(self.rules_dict.get("()", "#6A3DFF"))
        braces_format = make_format(self.rules_dict.get("{}", "#8E44AD"))
        brackets_format = make_format(self.rules_dict.get("[]", "#3A5BFF"))
        colon_format = make_format(self.rules_dict.get("{:}", "#B266FF"))

        self.rules.append((re.compile(r"[()]"), parens_format))
        self.rules.append((re.compile(r"[{}]"), braces_format))
        self.rules.append((re.compile(r"[\[\]]"), brackets_format))
        self.rules.append((re.compile(r":"), colon_format))

        # --- Comments ---
        comment_format = make_format("#6A9955")  # default green
        self.rules.append((re.compile(r"#.*"), comment_format))

    def highlightBlock(self, text: str):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)

class VariableViewer(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setIndentation(35)
        self.tree.setHeaderLabels(["Name", "Type", "Value"])
        header = self.tree.header()

        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.tree)

        # Define expandable container types
        self._expandable_types = {"list", "tuple", "set", "dict"}

    # ---- PUBLIC API ----
    def load_variables(self, variables: dict):
        """
        variables must be:
        {
            "var_name": value
        }
        """
        self.tree.clear()

        for name, value in variables.items():
            self._add_item(None, name, value)

    # ---- INTERNAL RECURSIVE LOGIC ----
    def _add_item(self, parent, name, value, level = 0):
        type_name = type(value).__name__

        # Create item
        if parent is None:
            item = QTreeWidgetItem(self.tree)
        else:
            item = QTreeWidgetItem(parent)

        if level == 0:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        item.setText(0, str(name))
        item.setText(1, type_name)

        # Expandable?
        if type_name in self._expandable_types:
            # Show summary in value column
            item.setText(2, self._summary(value))

            # Add children recursively
            if isinstance(value, dict):
                for k, v in value.items():
                    self._add_item(item, k, v, level+1)

            elif isinstance(value, (list, tuple)):
                for index, element in enumerate(value):
                    self._add_item(item, index, element, level+1)

            elif isinstance(value, set):
                for index, element in enumerate(value):
                    self._add_item(item, index, element, level+1)

        else:
            # Primitive — leaf node
            item.setText(2, repr(value))

    def _summary(self, value):
        """
        Returns short description for containers.
        """
        if isinstance(value, dict):
            return f"{len(value)} items"

        elif isinstance(value, (list, tuple, set)):
            return f"{len(value)} items"

        return ""
    
class Navigator(QWidget):
    file_open_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.placeholder = QLabel("No project folder selected.")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.placeholder)

        self.model = None
        self.tree = None

    def set_project_folder(self, path: str):
        # Clear existing widgets
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Create model
        self.model = QFileSystemModel()
        self.model.setRootPath(path)

        # Create tree
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(path))

        # Optional: hide extra columns
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        self.tree.hideColumn(3)

        self.tree.doubleClicked.connect(self._handle_double_click)

        self.layout.addWidget(self.tree)

    def _handle_double_click(self, index):
        if self.model.isDir(index):
            return

        path = self.model.filePath(index)
        self.file_open_requested.emit(path)