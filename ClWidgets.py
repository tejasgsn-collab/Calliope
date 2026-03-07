import sys

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFileSystemModel,QAction, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHeaderView,
    QLabel,
    QTreeView,
    QTextEdit,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QTabWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal, QProcess
from PyQt6.Qsci import QsciScintilla, QsciLexerPython

class CodeEditor(QsciScintilla):
    def __init__(self):
        super().__init__()
        

        self.configure_editor()

    def configure_editor(self):
        self.setMarginsForegroundColor(QColor("#858585"))
        self.setMarginsBackgroundColor(QColor("#1e1e1e"))
        self.setMarginWidth(0, "000")
        self.setStyleSheet("""
QsciScintilla {
    border: none;
    padding-left: 6px;
}
""")

        font = QFont("Consolas", 11)
        self.setFont(font)
        self.setMarginsFont(font)

        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#b9b9b9"))

        self.setIndentationGuides(True)
        self.setIndentationGuidesBackgroundColor(QColor("#264F78"))
        self.setIndentationGuidesForegroundColor(QColor("#FFFFFF"))

        self.setEdgeMode(QsciScintilla.EdgeMode.EdgeNone)

class TabWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(lambda index: self.tabs.removeTab(index))

        layout.addWidget(self.tabs)

        self.new_tab()

    # ---------- Tabs ----------

    def new_tab(self, name="Untitled", path=None):
        editor = CodeEditor(path)

        editor.modificationChanged.connect(
            lambda changed, e=editor: self._update_tab_title(e, changed)
        )

        self.tabs.addTab(editor, name)
        self.tabs.setCurrentWidget(editor)

        return editor

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

        self.model.setOption(QFileSystemModel.Option.DontWatchForChanges, True)
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

class ViewerWidget(QWidget):
    def __init__(self,variables: dict):
        super().__init__()
        self.viewer = QTableWidget()
        self.viewer.setColumnCount(3)
        self.viewer.setHorizontalHeaderLabels(["Name", "Type", "Value"])
        self.viewer.horizontalHeader().setStretchLastSection(True)
        self.viewer.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout = QVBoxLayout(self)
        layout.addWidget(self.viewer)

        for var,value in list(variables.items()):
            self.add_row(var,type(value).__name__,value)

    def add_row(self,name,type,value):
        containers = {"list","tuple","dict"}
        if type in containers:
            nos = len(value)
            value = f"Collect: length {nos}"
        
        row = self.viewer.rowCount()
        self.viewer.insertRow(row)

        self.viewer.setItem(row, 0, QTableWidgetItem(name))
        self.set_status_cell(row, type)
        self.viewer.setItem(row, 2, QTableWidgetItem(str(value)))

    def set_fixed_cell(self, row: int, col:int , text , colour:str):
        item = QTableWidgetItem(text)
        item.setBackground(QColor(colour))
        self.viewer.setItem(row, col, item)

    def set_status_cell(self, row, type):
        syntax_colors = {
    "str": "#98C379",
    "int": "#D19A66", 
    "float": "#D19A66",       
    "bool": "#0020AF",        
    "NoneType": "#C678DD",
    "list": "#FFFB00", 
    "dict": "#AE00FF",
    "function": "#D5E57B",
    "class": "#61AFEF"        
}
        # Color the Type column
        type_item = QTableWidgetItem(type)
        if type in syntax_colors:
            type_item.setBackground(QColor(syntax_colors[type]))
        self.viewer.setItem(row, 1, type_item)
        
        # Also color the Value column with the same color
        value_item = self.viewer.item(row, 2)
        if value_item and type in syntax_colors:
            value_item.setBackground(QColor(syntax_colors[type]))

    def remove_row(self,row):
        self.viewer.removeRow(row)