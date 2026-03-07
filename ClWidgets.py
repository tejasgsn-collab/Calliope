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

class CodeEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.editor = QsciScintilla()

        layout = QVBoxLayout(self)
        layout.addWidget(self.editor)

        self.configure_editor()

    def configure_editor(self):
        self.editor.setMarginsForegroundColor(QColor("#858585"))
        self.editor.setMarginsBackgroundColor(QColor("#1e1e1e"))
        self.editor.setMarginWidth(0, "000")
        self.editor.setStyleSheet("""
QsciScintilla {
    border: none;
    padding-left: 6px;
}
""")

        font = QFont("Consolas", 11)
        self.editor.setFont(font)
        self.editor.setMarginsFont(font)

        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QColor("#b9b9b9"))

        self.editor.setIndentationGuides(True)
        self.editor.setIndentationGuidesBackgroundColor(QColor("#264F78"))
        self.editor.setIndentationGuidesForegroundColor(QColor("#FFFFFF"))

        self.editor.setEdgeMode(QsciScintilla.EdgeMode.EdgeNone)

class ViewerWidget(QWidget):
    def __init__(self,variables):
        super().__init__()
        self.viewer = QTableWidget
        self.viewer.setColumnCount(3)
        self.viewer.setHorizontalHeaderLabels(["Name", "Type", "Value"])
        self.viewer.horizontalHeader().setStretchLastSection(True)
        self.viewer.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for var,value in list(variables.items()):
            self.add_row(var,type(eval(value)).__name__,value)

    def add_row(self,name,type,value):
        row = self.viewer.rowCount()
        self.viewer.insertRow(row)

        self.viewer.setItem(row, 0, QTableWidgetItem(name))
        self.viewer.setItem(row, 0, QTableWidgetItem(type))
        self.viewer.setItem(row, 0, QTableWidgetItem(value))

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
        a = 3.1
        item = QTableWidgetItem(type)

        for elem in syntax_colors:
            if elem == type:
                item.setBackground(QColor(syntax_colors[elem]))

        self.viewer.setItem(row, 2, item)

    def remove_row(self,row):
        self.viewer.removeRow(row)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setCentralWidget(CodeEditor())
    window.showMaximized()
    sys.exit(app.exec())