from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
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
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileSystemModel
from PyQt6.Qsci import QsciScintilla, QsciLexerPython

import re
import json
from pathlib import Path
import sys
import tempfile
import os


# =========================
# CODE EDITOR
# =========================

class Coder(QsciScintilla):
    def __init__(self, path=None):
        super().__init__()

        self.path = path

        lexer = QsciLexerPython()
        self.setLexer(lexer)

        # Line numbers
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "0000")

        # Auto indent
        self.setAutoIndent(True)

        # Tabs → spaces
        self.setIndentationsUseTabs(False)
        self.setIndentationWidth(4)

        # Brace matching
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)

        # Caret line highlight
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#2a2a2a"))

        self.setUtf8(True)

        self.setStyleSheet("font-family: Consolas; font-size: 11pt;")


# =========================
# TAB WIDGET
# =========================

class TabWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        layout.addWidget(self.tabs)

        self.new_tab()

    # ---------- Tabs ----------

    def new_tab(self, name="Untitled", path=None):
        editor = Coder(path)

        editor.modificationChanged.connect(
            lambda changed, e=editor: self._update_tab_title(e, changed)
        )

        self.tabs.addTab(editor, name)
        self.tabs.setCurrentWidget(editor)

        return editor

    def close_tab(self, index):
        self.tabs.removeTab(index)

    def iter_tabs(self):
        for i in range(self.tabs.count()):
            yield self.tabs.widget(i)

    def set_current_editor(self, editor):
        self.tabs.setCurrentWidget(editor)

    def current_editor(self):
        return self.tabs.currentWidget()

    # ---------- Title Handling ----------

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

    # ---------- File Handling ----------

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Python File",
            "",
            "Python Files (*.py);;All Files (*.*)"
        )

        if path:
            self.open_file(path)

    def open_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if already open
            for editor in self.iter_tabs():
                if editor.path == path:
                    self.set_current_editor(editor)
                    return

            editor = self.new_tab(os.path.basename(path), path)
            editor.setText(content)
            editor.setModified(False)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def save_file(self, save_as=False):
        editor = self.current_editor()
        if not editor:
            return

        original_path = editor.path

        if save_as or not original_path:
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
            content = editor.text()

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            editor.path = path
            editor.setModified(False)

            index = self.tabs.indexOf(editor)
            self.tabs.setTabText(index, os.path.basename(path))

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# =========================
# NAVIGATOR
# =========================

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
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.model = QFileSystemModel()
        self.model.setRootPath(path)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(path))

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


# =========================
# TERMINAL
# =========================

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

        self._input_start = 0
        self._running = False

        self.default_color = QColor("#FFFFFF")
        self.error_color = QColor("#FF5555")
        self.system_color = QColor("#888888")

        self.output.keyPressEvent = self._handle_keypress

    def write(self, text, level="stdout"):
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
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

    def start_session(self, banner_text=""):
        self.clear()
        if banner_text:
            self.write(banner_text, level="system")

        cursor = self.output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output.setTextCursor(cursor)

        self._input_start = cursor.position()
        self._running = True


# =========================
# RUNNER ENGINE (FIXED MINIMUM)
# =========================

class RunnerEngine:
    def __init__(self, tabs: TabWidget, console: TerminalWidget):
        self.tabs = tabs
        self.console = console

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._process_finished)

        # connect terminal input → process stdin
        self.console.input_submitted.connect(self._send_input)

    # =========================
    # RUN
    # =========================

    def run_file(self):
        editor = self.tabs.current_editor()
        if not editor:
            return

        code = editor.text()
        if not code.strip():
            self.console.write("[No code to run]\n", level="system")
            return

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
            if not var.startswith("__") and not callable(val):
                print(f"{{var}}|||{{repr(val)}}")
        print("__END_VAR_DUMP__")

        sys.stdout.flush()
        time.sleep(0.05)

except Exception as e:
    print("__ERROR__")
    print(e)
    sys.stdout.flush()
"""
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
        tmp.write(wrapped.encode("utf-8"))
        tmp.close()

        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()

        self.viewer.load_variables({})  # clear old vars
        self.console.start_session("$ python script.py\n")
        self.console.set_running(True)

        self.process.start(sys.executable, [tmp.name])

    # =========================
    # STOP
    # =========================

    def stop_run(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.console.write("\n[Process stopped]\n", level="system")

    # =========================
    # OUTPUT HANDLING
    # =========================

    def _read_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()

        lines = data.splitlines(keepends=True)

        collecting = False
        variables = {}

        for line in lines:
            stripped = line.strip()

            if stripped == "__VAR_DUMP__":
                collecting = True
                variables = {}
                continue

            if stripped == "__END_VAR_DUMP__":
                collecting = False
                self.viewer.load_variables(variables)
                continue

            if collecting:
                if "|||" in line:
                    name, value = line.strip().split("|||", 1)
                    try:
                        parsed = eval(value)
                    except:
                        parsed = value
                    variables[name] = parsed
            else:
                self.console.write(line)

    def _read_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.console.write(data, level="error")

    def _process_finished(self):
        self.console.write("\n[Process finished]\n", level="system")
        self.console.set_running(False)

    # =========================
    # INPUT HANDLING
    # =========================

    def _send_input(self, text: str):
        if self.process.state() == QProcess.ProcessState.Running:
            self.process.write((text + "\n").encode())