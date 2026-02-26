import sys
import tempfile
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Extensions import VariableViewer as VV, Highlighter as hltr, Navigator
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPlainTextEdit,
    QFileDialog,
    QSplitter ,
    QMessageBox,
    QToolBar,
    QTabWidget,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import  Qt, QProcess

class Vertigo(QMainWindow):
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

        # --- Editor ---

        self.tabs = QTabWidget()
        self.new_tab()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(
            "background-color:#000000; color:#ffffff; font-family: Consolas; font-size: 11pt;"
            )
        self.console.keyPressEvent = self._console_keypress

        self.navigator = Navigator()
        self.navigator.file_open_requested.connect(self.open_file)

        self.viewer = VV()

        editor = QSplitter(Qt.Orientation.Horizontal)
        editor.addWidget(self.tabs)
        editor.addWidget(self.viewer)
        editor.setSizes([400,150])

        Workbench = QSplitter(Qt.Orientation.Vertical)
        Workbench.addWidget(editor)
        Workbench.addWidget(self.console)
        Workbench.setSizes([294,126])

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.navigator)
        splitter.addWidget(Workbench)
        splitter.setSizes([200,600])
        self.setCentralWidget(splitter)

        self._create_menu()

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._process_finished)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)

    def new_tab(self,name = "Untitled",path = None):
        editor = QPlainTextEdit()
        editor.document().modificationChanged.connect(
        lambda changed, e=editor: self._update_tab_title(e, changed)
        )
        editor.setUndoRedoEnabled(True)
        editor.setStyleSheet("font-family: Consolas; font-size: 11pt;")
        editor.highlighter = hltr(editor.document())
        editor.path = path

        self.tabs.addTab(editor, name)
        self.tabs.setCurrentWidget(editor)

    def close_tab(self, index):
        self.tabs.removeTab(index)

    def open_project_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if not folder:
            return
        self.navigator.set_project_folder(folder)

    def _update_tab_title(self, editor, changed):
        index = self.tabs.indexOf(editor)
        if index == -1:
            return

        title = self.tabs.tabText(index)

    # Remove existing *
        if title.endswith("*"):
            title = title[:-1]

        if changed:
            title += "*"

        self.tabs.setTabText(index, title)

    def _create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        run_menu = menubar.addMenu("Run")

        open_action = QAction("Open File", self)
        open_action.triggered.connect(self.open_file)

        save_action = QAction("Save File", self)
        save_action.triggered.connect(self.save_file)

        open_folder = QAction("Open Folder", self)
        open_folder.triggered.connect(self.open_project_folder)

        run_action = QAction("Run File",self)
        run_action.triggered.connect(self.run_file)
        stop_action = QAction("Stop Execution", self)
        stop_action.triggered.connect(self.stop_run)

        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(open_folder)

        run_menu.addAction(run_action)
        run_menu.addAction(stop_action)

    def _read_stdout(self):
        raw = self.process.readAllStandardOutput().data().decode()

        for line in raw.splitlines():
            line = line.rstrip()
            if line == "__VAR_DUMP__":
                self._var_dump_mode = True
                self.Variables.clear()
                continue

            if self._var_dump_mode:
                parts = line.split("|||")
                if len(parts) == 3:
                    name, typ, value = parts
                    self.Variables[name] = value
                continue
            self._console_append(line)

        self._input_start = self.console.textCursor().position()


    def _read_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self._console_append(data)
        self._input_start = self.console.textCursor().position()

    def _process_finished(self):
        try:
            self._var_dump_mode = False
            self._console_append("\n[Process finished]")
            self.viewer.load_variables(self.Variables)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


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

    def iter_tabs(self):
            for i in range(self.tabs.count()):
                yield self.tabs.widget(i)
    def set_current_editor(self, editor):
        self.tabs.setCurrentWidget(editor)
    def current_editor(self):
        return self.tabs.currentWidget()

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

    def open_file(self,path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            for editor in self.iter_tabs():
                if editor.path == path:
                    self.set_current_editor()
                    return

            self.new_tab(os.path.basename(path))
            self.path = path

            editor = self.tabs.currentWidget()
            editor.setPlainText(content)
            editor.document().setModified(False)

            self.statusBar().showMessage(f"Opened: {path}", 3000)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def save_file(self):
        if not self.path:
            QMessageBox.warning(self, "No File", "Open a file first.")
            return
        try:
            editor = self.tabs.currentWidget()
            content = editor.toPlainText()
            with open(self.current_editor().path, "w", encoding="utf-8") as f:
                f.write(content)
            self.statusBar().showMessage("File saved", 2000)
            editor.document().setModified(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def stop_run(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.console.appendPlainText("\n[Process stopped]")


    def run_file(self):
        """Run current editor contents in a background Python process."""
        editor = self.tabs.currentWidget()
        if not isinstance(editor, QPlainTextEdit):
            return
        code = editor.toPlainText()

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

    def show_variables(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Vertigo("Test 1")
    window.showMaximized()
    sys.exit(app.exec())