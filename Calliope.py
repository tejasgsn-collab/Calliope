"""
This is an restart of my old project, Calliope, now taking advantege of the fact that it is now stored on GitHub. It is an (Currently) Python-based IDE that makes development of Python projects easier for beginners.
"""
from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QVBoxLayout,
    QSplitter,
    QFileDialog
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from ClWidgets import *
import sys

class Calliope(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calliope IDE")
        self.resize(800, 600)
        self.editor = CodeEditor()
        self.viewer = ViewerWidget({"a":1,"b":"hello world","c":[1,2,3]})
        self.splitter = QSplitter()
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.viewer)
        self.splitter.setSizes([400, 400])
        self.setCentralWidget(self.splitter)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Calliope()
    window.showMaximized()
    sys.exit(app.exec())