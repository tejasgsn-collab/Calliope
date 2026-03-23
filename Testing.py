from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget
import sys

class Demowin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.counter = 1

        self.button = QPushButton("Add Label")
        self.Area = QScrollArea()
        self.Area.setWidgetResizable(True)

        # Scroll area content
        intermediate = QWidget()
        self.Layout = QVBoxLayout()
        intermediate.setLayout(self.Layout)
        self.Area.setWidget(intermediate)

        # Main layout
        self.main = QVBoxLayout()
        self.main.addWidget(self.Area)
        self.main.addWidget(self.button)

        # FIX: wrap layout in QWidget
        container = QWidget()
        container.setLayout(self.main)
        self.setCentralWidget(container)

        self.button.clicked.connect(self.addlabel)

    def addlabel(self):
        templabel = QLabel(f"Label no.{self.counter}")
        self.Layout.addWidget(templabel)
        self.counter += 1

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Demowin()
    window.showMaximized()
    sys.exit(app.exec())