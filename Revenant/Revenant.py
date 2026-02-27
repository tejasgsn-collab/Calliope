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

from Extensions import *

import sys


class Revenant(QMainWindow):
    def __init__(self, title="Revenant"):
        super().__init__()

        self.setWindowTitle(title)

        # =========================
        # Core Components
        # =========================
        self.navigator = Navigator()
        self.tabs = TabWidget()
        self.viewer = VariableViewer()
        self.console = TerminalWidget()

        self.runner = RunnerEngine(self.tabs, self.console, self.viewer)

        # =========================
        # Layout Construction
        # =========================

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # Horizontal splitter (Navigator | Editor/Right side)
        horizontal_split = QSplitter(Qt.Orientation.Horizontal)

        # Vertical splitter (Editor | Bottom panel)
        vertical_split = QSplitter(Qt.Orientation.Vertical)

        # Bottom splitter (Variables | Terminal)
        bottom_split = QSplitter(Qt.Orientation.Horizontal)

        # Assemble layout
        horizontal_split.addWidget(self.navigator)

        vertical_split.addWidget(self.tabs)

        bottom_split.addWidget(self.viewer)
        bottom_split.addWidget(self.console)

        vertical_split.addWidget(bottom_split)

        horizontal_split.addWidget(vertical_split)

        main_layout.addWidget(horizontal_split)

        # Set initial proportions
        horizontal_split.setSizes([250, 1000])
        vertical_split.setSizes([700, 300])
        bottom_split.setSizes([400, 600])

        # =========================
        # Connections
        # =========================
        self.navigator.file_open_requested.connect(self.tabs.open_file)

        # =========================
        # Menu
        # =========================
        self._create_menu()

    # =========================
    # MENU
    # =========================

    def _create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        run_menu = menubar.addMenu("Run")

        # ---- File Actions ----
        open_action = QAction("Open File", self)
        open_action.triggered.connect(self.tabs.open_file_dialog)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.tabs.save_file)

        save_as_action = QAction("Save As", self)
        save_as_action.triggered.connect(lambda: self.tabs.save_file(True))

        open_folder_action = QAction("Open Folder", self)
        open_folder_action.triggered.connect(self.open_project_folder)

        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addAction(open_folder_action)

        # ---- Run Actions ----
        run_action = QAction("Run File", self)
        run_action.triggered.connect(self.runner.run_file)

        stop_action = QAction("Kill Program", self)
        stop_action.triggered.connect(self.runner.stop_run)

        run_menu.addAction(run_action)
        run_menu.addAction(stop_action)

    # =========================
    # PROJECT FOLDER
    # =========================

    def open_project_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if path:
            self.navigator.set_project_folder(path)


# =========================
# APP ENTRY
# =========================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Revenant("Revenant IDE")
    window.showMaximized()
    sys.exit(app.exec())