from PyQt5.QtWidgets import QTreeWidgetItem
from .utility import to_time_string
from PyQt5.QtCore import Qt


class WidgetItem(QTreeWidgetItem):
    def __init__(self, parent=None, data=None):
        QTreeWidgetItem.__init__(self, parent)
        self.data = data
        self.has_data = self.data is not None
        self.collide = None
        self.state = ''
        if self.has_data:
            self.collide = self.data['collide']
            del self.data['collide']
            if self.collide:
                self.state = '已匯入'

    def refresh_content(self):
        if self.collide or self.state == '完成':
            if not self.isDisabled():
                self.setDisabled(True)

        self.setText(0, self.data['name'])
        self.setText(1, self.get_state())
        self.setText(2, self.data['type'])

        if not self.collide:
            self.setText(3, '{:.1f}m'.format(self.data['size'] / 1024 / 1024))
            self.setText(4, '{}x{}'.format(self.data['width'], self.data['height']))
            self.setText(5, to_time_string(self.data['duration']))
            self.setText(6, ', '.join(self.data['tag']))
            self.setText(7, self.data['parent'])

    def __lt__(self, otherItem):
        column = self.treeWidget().sortColumn()
        try:
            return float(self.text(column)[:-1]) > float(otherItem.text(column)[:-1])
        except ValueError:
            return self.text(column) > otherItem.text(column)

    def is_active(self):
        return self.has_data and not self.collide

    def is_importable(self):
        return self.is_active() and self.checkState(0) == Qt.Checked

    def get_state(self):
        if self.isDisabled():
            return self.state
        if not self.has_data:
            return ''
        elif self.collide:
            return '已匯入'
        elif self.checkState(0) != Qt.Checked:
            return '忽略'
        elif self.state == '':
            return '佇列'
        else:
            return self.state
