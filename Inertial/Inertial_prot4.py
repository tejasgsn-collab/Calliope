import sys
import tempfile
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPlainTextEdit,
    QFileDialog,
    QSplitter ,
    QMessageBox,
    QToolBar,
    QLabel
)
from PyQt6.QtGui import QAction, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import  Qt, QProcess
import re
import json

class PythonHighlighter(QSyntaxHighlighter):

    def __init__(self, document):
        super().__init__(document)
        with open("Format.json","r") as f:
            self.rules_dict = json.load(f)
        def make_format(color):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            return fmt
        self.rules = []
        keyword_format = make_format("#2f00ff")
        keywords = self.rules_dict["pykeywords"]
        for kw in keywords:
            pattern = r"\b" + kw + r"\b"
            self.rules.append((re.compile(pattern), keyword_format))

        number_format = make_format("#d6d301")
        self.rules.append((re.compile(r"\b\d+\b"), number_format))

        string_format = make_format("#138513")
        self.rules.append((re.compile(r'".*?"'), string_format))
        self.rules.append((re.compile(r"'.*?'"), string_format))


    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)



class Inertial(QMainWindow):
    """
    Inertial is a Qt-based GUI app that serves as an initial prototype
    of the Calliope IDE project. It allows editing and saving Python programs.
    """

    def __init__(self, name):
        super().__init__()
        self.Variables = {}
        self._var_dump_mode = False

        self.setWindowTitle(name)
        self.resize(800, 420)

        self.path: str|None = None
        self.filename = None

        self.file_bar = QToolBar()
        self.addToolBar(self.file_bar)

        # Label to show file name
        self.file_label = QLabel("No file loaded")
        self.file_bar.addWidget(self.file_label)

        # --- Editor ---
        self.editor = QPlainTextEdit()
        self.editor.setUndoRedoEnabled(True)
        self.editor.setStyleSheet("font-family: Consolas; font-size: 11pt;")

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background:#111; color:#0f0; font-family: Consolas; font-size: 11pt;")
        self.console.keyPressEvent = self._console_keypress


        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.console)
        splitter.setSizes([500, 300])

        self.setCentralWidget(splitter)
        self.highlighter = PythonHighlighter(self.editor.document())
        # --- Menu ---
        self._create_menu()

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._process_finished)

        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)

    # -------------------------
    # Menu Setup
    # -------------------------
    def _create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        run_menu = menubar.addMenu("Run")

        open_action = QAction("Open File", self)
        open_action.triggered.connect(self.open_file)

        save_action = QAction("Save File", self)
        save_action.triggered.connect(self.save_file)

        run_action = QAction("Run",self)
        run_action.triggered.connect(self.run_file)
        stop_action = QAction("Stop", self)
        stop_action.triggered.connect(self.stop_run)

        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        run_menu.addAction(run_action)
        run_menu.addAction(stop_action)

    def _read_stdout(self):
        raw = self.process.readAllStandardOutput().data().decode()

        for line in raw.splitlines():

            line = line.rstrip()

        # --- detect start of variable dump ---
            if line == "__VAR_DUMP__":
                self._var_dump_mode = True
                self.Variables.clear()
                continue

        # --- parse variable lines ---
            if self._var_dump_mode:
                parts = line.split("|||")
                if len(parts) == 3:
                    name, typ, value = parts
                    self.Variables[name] = (typ, value)
                continue   # don't print dump lines

        # --- normal output ---
            self._console_append(line)

        self._input_start = self.console.textCursor().position()


    def _read_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self._console_append(data)
        self._input_start = self.console.textCursor().position()

    def _process_finished(self):
        self._var_dump_mode = False
        self._console_append("\n[Process finished]")
        print("Captured Variables:", self.Variables)


    def _console_keypress(self, event):
        if self.process.state() != QProcess.ProcessState.Running:
            return

        cursor = self.console.textCursor()

    # block cursor moving above input zone
        if cursor.position() < self._input_start:
            cursor.setPosition(self._input_start)
            self.console.setTextCursor(cursor)

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor.movePosition(cursor.MoveOperation.End)
            self.console.setTextCursor(cursor)

            text = self.console.toPlainText()[self._input_start:]
            self.process.write((text + "\n").encode())

            self._console_append("")  # newline visually
            self._input_start = self.console.textCursor().position()
            return

    # allow typing only at end
        if event.key() == Qt.Key.Key_Backspace and cursor.position() <= self._input_start:
            return

        self.console.setReadOnly(False)
        QPlainTextEdit.keyPressEvent(self.console, event)
        self.console.setReadOnly(True)

    def _console_append(self, text):
        self.console.setReadOnly(False)
        self.console.appendPlainText(text)
        self.console.setReadOnly(True)

        cursor = self.console.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.console.setTextCursor(cursor)



    # -------------------------
    # File Handling
    # -------------------------
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Python File",
            "",
            "Python Files (*.py);;All Files (*.*)"
        )

        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            self.editor.setPlainText(content)
            self.path = path
            ne = self.path.split("/")[-1]
            self.file_label.setText(f"{ne}")
            self.statusBar().showMessage(f"Opened: {path}", 3000)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def save_file(self):
        if not self.path:
            QMessageBox.warning(self, "No File", "Open a file first.")
            return
        try:
            content = self.editor.toPlainText()
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(content)
            self.statusBar().showMessage("File saved", 2000)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def stop_run(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.console.appendPlainText("\n[Process stopped]")


    def run_file(self):
        """Run current editor contents in a background Python process."""

        code = self.editor.toPlainText()

        if not code.strip():
            self._console_append("[No code to run]\n")
            return

    # write temp script file
        safe = repr(code)

        wrapped = f"""
namespace = {{}}
try:
    exec({safe}, namespace)
except Exception as e:
    print("__Error_Occured__")
    print(e)

print("__VAR_DUMP__")
for var, dat in namespace.items():
    if not var.startswith("__"):
        print(f"{{var}}|||{{type(dat).__name__}}|||{{repr(dat)}}")
"""
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
        tmp.write(wrapped.encode("utf-8"))
        tmp.close()

    # clear console and start
        self.console.clear()
        self._console_append("[Running...]\n")
        self._input_start = self.console.textCursor().position()

    # stop previous run if still active
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()

    # start python subprocess
        self.process.start(sys.executable, [tmp.name])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Inertial("Test 1")
    window.show()
    sys.exit(app.exec())