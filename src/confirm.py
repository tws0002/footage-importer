from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5.QtCore import Qt
import os


ui_path = os.path.join(os.path.dirname(__file__), 'confirm.ui')


class ConfirmDialog(QDialog):
    def __init__(self, text, okonly=False, top=False):
        if top:
            flags = (Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        else:
            flags = (Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        super().__init__(None, flags)
        uic.loadUi(ui_path, self)
        self.context_text.setText(text)
        self.apply_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.close)
        if okonly:
            self.cancel_button.hide()
