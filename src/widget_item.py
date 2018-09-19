from PyQt5.QtWidgets import QTreeWidgetItem
from .utility import to_time_string
from PyQt5.QtCore import Qt


state_map = {
    'collide': '已匯入',
    'command': '解析錯誤',
    'size': '尺寸過小',
    'duration': '長度不符'
}


class WidgetItem(QTreeWidgetItem):
    def __init__(self, parent=None, data=None):
        QTreeWidgetItem.__init__(self, parent)
        self.data = data
        self.has_data = self.data is not None
        self.error = None
        self.state = ''
        self.root = ''
        if self.has_data:
            if self.data['error'] != 'null':
                self.error = self.data['error']
                self.state = state_map[self.error]
            self.root = self.data['root']
            del self.data['error']
            del self.data['root']

    def refresh_content(self):
        if self.error or self.state == '完成':
            if not self.isDisabled():
                self.setDisabled(True)

        self.setText(0, self.data['name'])
        self.setText(1, self.get_state())
        self.setText(2, self.data['type'])
        self.setText(3, '{:.1f}m'.format(self.data['size'] / 1024 / 1024))
        self.setText(7, self.data['parent'])

        if 'width' in self.data:
            self.setText(4, '{}x{}'.format(self.data['width'], self.data['height']))
        if 'duration' in self.data:
            self.setText(5, to_time_string(self.data['duration']))
        if 'tag' in self.data:
            self.setText(6, ', '.join(self.data['tag']))

    def __lt__(self, otherItem):
        column = self.treeWidget().sortColumn()
        try:
            return float(self.text(column)[:-1]) > float(otherItem.text(column)[:-1])
        except ValueError:
            return self.text(column) > otherItem.text(column)

    def is_active(self):
        return self.has_data and not self.isDisabled()

    def is_importable(self):
        return self.is_active() and self.checkState(0) == Qt.Checked

    def get_state(self):
        if self.isDisabled():
            return self.state

        if not self.has_data:
            return ''
        elif self.checkState(0) != Qt.Checked:
            return '忽略'
        elif self.state == '':
            return '佇列'
        else:
            return self.state
