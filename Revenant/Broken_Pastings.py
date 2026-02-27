from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFileSystemModel, QTextCursor
from PyQt6.QtWidgets import (
    QWidget, 
    QTreeWidget, 
    QTreeWidgetItem, 
    QVBoxLayout, 
    QHeaderView, 
    QLabel, 
    QTreeView, 
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QTabWidget
    )
from PyQt6.QtCore import Qt, pyqtSignal, QProcess
from PyQt6.Qsci import QsciScintilla, QsciLexerPython
import re
import json
from pathlib import Path
import sys
import tempfile
import sys
import os

class coder(QWidget):
    def __init__(self):
        super().__init__()
        self.editor = QsciScintilla()

        layout = QVBoxLayout(self)
        lexer = QsciLexerPython()
        self.editor.setLexer(lexer)
# Line numbers
        self.editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.editor.setMarginWidth(0, "0000")
# Auto indent
        self.editor.setAutoIndent(True)
# Tabs → spaces
        self.editor.setIndentationsUseTabs(False)
        self.editor.setIndentationWidth(4)
# Brace matching
        self.editor.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)

# Caret line highlight
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QColor("#2a2a2a"))
# UTF-8
        self.editor.setUtf8(True)
        layout.addWidget(self.editor)

class TabWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.tabs = QTabWidget()
        self.new_tab()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

    def new_tab(self,name = "Untitled",path = None):
        editor = coder()
        editor.modificationChanged.connect(
        lambda changed, e=editor: self._update_tab_title(e, changed)
        )
        editor.setUndoRedoEnabled(True)
        editor.path = path
        editor.setStyleSheet("font-family: Consolas; font-size: 11pt;")

        self.tabs.addTab(editor, name)
        self.tabs.setCurrentWidget(editor)
    
    def close_tab(self, index):
        self.tabs.removeTab(index)

    def _update_tab_title(self, editor, changed):
        index = self.tabs.indexOf(editor)
        if index == -1:
            return

        title = self.tabs.tabText(index)

        if title.endswith("*"):
            title = title[:-1]

        if changed:
            title += "*"

        self.tabs.setTabText(index, title)

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
        self,
        "Open Python File",
        "",
        "Python Files (*.py);;All Files (*.*)"
    )
        if not path:
            return

        self.open_file(path)

    def iter_tabs(self):
            for i in range(self.tabs.count()):
                yield self.tabs.widget(i)

    def set_current_editor(self, editor):
        self.tabs.setCurrentWidget(editor)

    def current_editor(self):
        return self.tabs.currentWidget()

    def open_file(self,path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            for editor in self.iter_tabs():
                if editor.path == path:
                    self.set_current_editor(editor)
                    return

            self.new_tab(os.path.basename(path))
            self.path = path

            editor = self.tabs.currentWidget()
            editor.path = path
            editor.setText(content)
            editor.setModified(False)

            self.statusBar().showMessage(f"Opened: {path}", 3000)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def save_file(self, SaveAs: bool = False):
        editor: QTextEdit = self.current_editor()
        if not editor:
            return

        original_path = getattr(editor, "path", None)

    # Decide if Save As dialog is needed
        if SaveAs or not original_path:
            path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            original_path or "",
            "Python Files (*.py);;All Files (*.*)"
        )

            if not path:
                return
        else:
            path = original_path

        try:
            content = editor.toPlainText()

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            if SaveAs:
            # Create NEW tab for the new file
                self.new_tab(os.path.basename(path), path)
                new_editor = self.current_editor()
                new_editor.setText(content)
                new_editor.setModified(False)
            else:
            # Normal Save — update existing tab
                editor.setModified(False)

                index = self.tabs.indexOf(editor)
                self.tabs.setTabText(index, os.path.basename(path))

            self.statusBar().showMessage("File saved", 2000)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

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

class TerminalWidget(QWidget):
    input_submitted = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.output = QTextEdit()
        self.output.setStyleSheet(
            "background-color:#000000; color:#ffffff; font-family: Consolas; font-size: 11pt;"
        )
        layout.addWidget(self.output)

        # Internal state
        self._input_start = 0
        self._running = False

        # Colors
        self.default_color = QColor("#FFFFFF")
        self.error_color = QColor("#FF5555")
        self.system_color = QColor("#888888")

        # Override keypress
        self.output.keyPressEvent = self._handle_keypress

    def write(self, text, level="stdout"):
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output.setTextCursor(cursor)

        if level == "error":
            self.output.setTextColor(self.error_color)
        elif level == "system":
            self.output.setTextColor(self.system_color)
        else:
            self.output.setTextColor(self.default_color)

        self.output.insertPlainText(text)
        self.output.ensureCursorVisible()

    def clear(self):
        self.output.clear()
        self._input_start = 0

    def set_running(self, running: bool):
        self._running = running

    def _handle_keypress(self, event):
        cursor = self.output.textCursor()

        # Always keep cursor at end if running
        if self._running:
            if cursor.position() < self._input_start:
                cursor.setPosition(self._input_start)
                self.output.setTextCursor(cursor)

            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.output.setTextCursor(cursor)

                text = self.output.toPlainText()[self._input_start:]

                # Emit signal instead of writing to process directly
                self.input_submitted.emit(text)

                self.output.insertPlainText("\n")

                cursor = self.output.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.output.setTextCursor(cursor)
                self._input_start = cursor.position()
                return

            if event.key() == Qt.Key.Key_Backspace and cursor.position() <= self._input_start:
                return

        QTextEdit.keyPressEvent(self.output, event)

    def start_session(self, banner_text=""):
        self.clear()
        if banner_text:
            self.write(banner_text, level="system")

        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output.setTextCursor(cursor)

        self._input_start = cursor.position()
        self._running = True

class RunnerEngine():
    def __init__():
        pass
    def stop_run(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.console.appendPlainText("\n[Process stopped]")
    def run_file(self):
        """Run current editor contents in a background Python process."""
        editor = self.tabs.currentWidget()
        if not isinstance(editor, QTextEdit):
            return
        code = editor.toPlainText()

        if not code.strip():
            self.console.write("[No code to run]\n")
            return

    # write temp script file
        safe = repr(code)

        wrapped = f"""
import ast
import sys
import time

code = {safe}
namespace = {{}}

try:
    tree = ast.parse(code)

    for node in tree.body:
        single = ast.Module(body=[node], type_ignores=[])
        compiled = compile(single, "<vertigo>", "exec")
        exec(compiled, namespace)

        print("__VAR_DUMP__")
        for var, val in namespace.items():
            if not var.startswith("__") and not callable(var):
                print(f"{{var}}|||{{type(val).__name__}}|||{{repr(val)}}")
        print("__END_VAR_DUMP__")

        sys.stdout.flush()
        time.sleep(0.15)

except Exception as e:
    print("__Error_Occured__")
    print(e)
    sys.stdout.flush()
"""
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
        tmp.write(wrapped.encode("utf-8"))
        tmp.close()

    # clear console and start
        self.console.clear()
        self.console.start_session("$ python script.py\n")

        cursor = self.console.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.console.setTextCursor(cursor)
        self._input_start = cursor.position()

        self._input_start = self.console.textCursor().position()

    # stop previous run if still active
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()

    # start python subprocess
        self.process.start(sys.executable, [tmp.name])