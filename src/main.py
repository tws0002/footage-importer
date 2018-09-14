from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtCore import Qt
import os
from .tag_edit import TagEditor
from .confirm import ConfirmDialog
from .progress import ParsePath, ImportResource
from .widget_item import WidgetItem
import pickle


ui_path = os.path.join(os.path.dirname(__file__), 'main.ui')
debug_file = 'debug_items.pickle'


class FootageImporter(QMainWindow):
    def __init__(self, debug=False):
        super().__init__()
        uic.loadUi(ui_path, self)

        self.freeze_group = [
            self.import_button,
            self.path_text,
            self.file_button,
            self.edit_tag_button,
            self.toggle_tick_button,
            self.flat_toggle
        ]

        self.edit_group = [
            self.edit_tag_button,
            self.toggle_tick_button,
        ]
        for qt in self.edit_group:
            qt.setDisabled(True)

        self.progress = None
        self.parse_path = ParsePath(self)
        self.import_resource = ImportResource(self)

        self.parents = {}
        self.items = []
        self.title = self.windowTitle()
        self.debug = debug

        self.progress_bar.hide()
        self.cancel_button.hide()

        self.flat_toggle.clicked.connect(self.on_flat_toggle_click)
        self.file_button.clicked.connect(self.on_file_click)
        self.edit_tag_button.clicked.connect(self.on_tag_edit_click)
        self.toggle_tick_button.clicked.connect(self.on_toggle_tick_click)
        self.import_button.clicked.connect(self.on_import_click)
        self.cancel_button.clicked.connect(self.on_cancel_click)
        self.path_text.textChanged.connect(self.on_path_changed)
        self.edit_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.edit_tree.itemDoubleClicked.connect(self.on_item_double_click)
        self.edit_tree.itemChanged.connect(self.on_item_changed)

        if self.debug and os.path.isfile(debug_file):
            with open(debug_file, 'rb') as f:
                objs = pickle.load(f)
                for obj in objs:
                    self.add_item(obj)
                self.refresh_tree()

    def on_file_click(self):
        path = str(QFileDialog.getExistingDirectory(self, "選擇素材資料夾"))
        self.path_text.setText(path)

    def on_tag_edit_click(self):
        tags = []
        for item in self.edit_tree.selectedItems():
            if item.is_active():
                if len(tags) == 0:
                    tags.extend(item.data['tag'])
                else:
                    tags = sorted(list(set(tags).intersection(item.data['tag'])))

        tagEditor = TagEditor(tags)
        if tagEditor.exec_():
            for item in self.edit_tree.selectedItems():
                if item.is_active():
                    for action in tagEditor.actions:
                        text = action['text']
                        if action['type'] == 'add':
                            if text not in item.data['tag']:
                                item.data['tag'].append(text)
                        else:
                            if text in item.data['tag']:
                                item.data['tag'].remove(text)
                    if len(tagEditor.actions) > 0:
                        item.data['tag'] = sorted(item.data['tag'])

    def on_path_changed(self, path):
        if os.path.isdir(path):
            self.edit_tree.clear()
            self.parse_path.start_func(path)

    def on_selection_changed(self):
        items = self.edit_tree.selectedItems()
        for button in self.edit_group:
            button.setEnabled(len(items) > 0)

    def on_item_double_click(self, item):
        if item.has_data:
            os.startfile(item.data['raw'])
        elif item.parent() is None:
            root_path = os.path.split(self.path_text.text())
            os.startfile(root_path[0] + '/' + item.text(0) + '/')

    def on_toggle_tick_click(self):
        active_ratio = 0
        parent_ratio = 0
        has_active = False

        items = self.edit_tree.selectedItems()
        for item in items:
            if item.is_active():
                has_active = True
            if item.has_data:
                active_ratio += -1 if item.checkState(0) == Qt.Unchecked else 1
            else:
                parent_ratio += -1 if item.checkState(0) == Qt.Unchecked else 1

        for item in items:
            if item.is_active():
                checkState = Qt.Checked if active_ratio < 0 else Qt.Unchecked
                item.setCheckState(0, checkState)
            elif not has_active and not item.has_data:
                checkState = Qt.Checked if parent_ratio < 0 else Qt.Unchecked
                item.setCheckState(0, checkState)

    def on_import_click(self, direct=False):
        import_objs = []
        for item in self.items:
            if item.is_importable():
                import_objs.append(item)
        if len(import_objs) == 0:
            confirm = ConfirmDialog('沒有可匯入的素材！', True)
            if confirm.exec_():
                pass
            return

        if direct:
            self.import_resource.start_func(import_objs)
        else:
            confirm = ConfirmDialog('確定要匯入這 {} 個素材嗎？'.format(len(import_objs)))
            if confirm.exec_():
                self.import_resource.start_func(import_objs)

    def on_cancel_click(self):
        self.progress.cancel = True

    def progress_start(self):
        for qt in self.freeze_group:
            qt.setDisabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(10000)
        self.progress_bar.show()
        self.cancel_button.show()

    def progress_max(self, val):
        self.progress_bar.setMaximum(val)
        self.progress_bar.setValue(0)

    def progress_inc(self):
        self.progress_bar.setValue(self.progress_bar.value() + 1)

    def progress_log(self, text):
        self.log_text.setText(text)

    def progress_done(self):
        self.setWindowTitle(self.title)
        self.progress_bar.hide()
        self.cancel_button.hide()
        for qt in self.freeze_group:
            qt.setDisabled(False)
        self.progress = None

    def add_item(self, obj):
        if obj['parent'] in self.parents:
            parent_item = self.parents[obj['parent']]
        else:
            parent_item = WidgetItem(self.edit_tree)
            parent_item.setExpanded(True)
            parent_item.setText(0, obj['parent'])
            parent_item.setFlags(parent_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            self.parents[obj['parent']] = parent_item

        item = WidgetItem(parent_item, obj)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(0, Qt.Checked)
        self.items.append(item)

    def prompt(self, text):
        confirm = ConfirmDialog(text, True, True)
        if confirm.exec_():
            pass
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()

    def refresh_tree(self):
        for i in range(self.edit_tree.columnCount()):
            self.edit_tree.resizeColumnToContents(i)
            size = self.edit_tree.columnWidth(i)

            offset = 20 if i != self.edit_tree.columnCount() - 1 else 0
            self.edit_tree.setColumnWidth(i, size + offset)

        self.edit_tree.sortByColumn(0, Qt.SortOrder.DescendingOrder)

    def item_change_state(self, item, state):
        item.state = state
        self.on_item_changed(item, 0)

    def changeTitle(self, text):
        self.setWindowTitle(self.title + '  >>  ' + text)

    def save_items(self):
        objs = []
        for item in self.items:
            data = item.data
            data['collide'] = item.collide
            objs.append(data)

        with open(debug_file, 'wb') as f:
            pickle.dump(objs, f, protocol=pickle.HIGHEST_PROTOCOL)

    def on_flat_toggle_click(self, flat):
        for i in range(self.edit_tree.topLevelItemCount() - 1, -1, -1):
            self.edit_tree.takeTopLevelItem(i)
        if flat:
            header = self.edit_tree.headerItem()
            header.setText(self.edit_tree.columnCount(), '資料夾')
            for parent in self.parents.values():
                parent.takeChildren()
            self.edit_tree.addTopLevelItems(self.items)
        else:
            self.edit_tree.setColumnCount(self.edit_tree.columnCount() - 1)
            self.edit_tree.addTopLevelItems(self.parents.values())
            for item in self.items:
                self.parents[item.data['parent']].addChild(item)
            for parent in self.parents.values():
                parent.setExpanded(True)
        self.refresh_tree()

    def on_item_changed(self, item, column):
        if item.has_data:
            item.refresh_content()
