from PyQt5.QtWidgets import QDialog, QListWidgetItem
from PyQt5 import uic
from PyQt5.QtCore import Qt
import os
from .tag_add import TagAddInput


ui_path = os.path.join(os.path.dirname(__file__), 'tag_edit.ui')


class TagEditor(QDialog):
    def __init__(self, tags):
        super().__init__(None, Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        uic.loadUi(ui_path, self)
        self.apply_button.clicked.connect(self.accept)
        self.add_button.clicked.connect(self.on_add_click)
        self.del_button.clicked.connect(self.on_del_click)

        self.actions = []

        for tag in tags:
            item = QListWidgetItem(self.tag_list)
            item.setText(tag)

    def on_del_click(self):
        for item in self.tag_list.selectedItems():
            self.actions.append({
                'type': 'del',
                'text': item.text()
            })
            self.tag_list.takeItem(self.tag_list.row(item))

    def on_add_click(self):
        tag_input = TagAddInput()
        if tag_input.exec_():
            text = tag_input.input_text.text().lower()

            count = self.tag_list.count()
            for i in range(count):
                if text == self.tag_list.item(i).text():
                    return
            if text != '':
                item = QListWidgetItem(self.tag_list)
                item.setText(text)
                self.actions.append({
                    'type': 'add',
                    'text': text
                })
