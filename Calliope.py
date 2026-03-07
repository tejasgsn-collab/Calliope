"""
This is an restart of my old project, Calliope, now taking advantege of the fact that it is now stored it GitHub. It is an (Currently) Python-based IDE that makes development of Python projects easier for beginners.
"""
from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QFileDialog
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
import sys

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFileSystemModel
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
    QTabWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal, QProcess
from PyQt6.QtGui import QAction
from PyQt6.Qsci import QsciScintilla, QsciLexerPython

import re
import json
from pathlib import Path
import sys
import tempfile
import os

class Calliope(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calliope IDE")
        self.resize(800, 600)
        