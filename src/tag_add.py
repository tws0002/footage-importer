from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5.QtCore import Qt
import os


ui_path = os.path.join(os.path.dirname(__file__), 'tag_add.ui')


class TagAddInput(QDialog):
    def __init__(self):
        super().__init__(None, Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        uic.loadUi(ui_path, self)
        self.apply_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.close)
