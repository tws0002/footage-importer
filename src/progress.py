from PyQt5.QtCore import QThread, pyqtSignal
from .db import parse_path, import_resource


class Progress(QThread):
    sig_max = pyqtSignal(int)
    sig_inc = pyqtSignal()
    sig_log = pyqtSignal(str)
    sig_title = pyqtSignal(str)
    sig_prompt = pyqtSignal(str)

    def __init__(self, parent, func):
        QThread.__init__(self)
        self.parent = parent
        self.func = func
        self.args = None
        self.name = ''
        self.cancel = False
        self.connect_signal()

    def connect_signal(self):
        self.started.connect(self.parent.progress_start)
        self.sig_inc.connect(self.parent.progress_inc)
        self.sig_max.connect(self.parent.progress_max)
        self.sig_log.connect(self.parent.progress_log)
        self.sig_prompt.connect(self.parent.prompt)
        self.sig_title.connect(self.parent.changeTitle)
        self.finished.connect(self.parent.progress_done)

    def run(self):
        self.cancel = False
        self.parent.progress = self
        self.sig_title.emit(self.name)
        self.before_run()
        self.func(self, *self.args)
        self.after_run()

    def start_func(self, *args):
        self.args = args
        self.start()

    def before_run(self):
        pass

    def after_run(self):
        pass


class ParsePath(Progress):
    sig_add_item = pyqtSignal(dict)
    sig_refresh_tree = pyqtSignal()
    sig_save_items = pyqtSignal(bool)
    sig_run_import = pyqtSignal(bool)

    def __init__(self, parent):
        Progress.__init__(self, parent, parse_path)
        self.name = '解析路徑...'

    def connect_signal(self):
        Progress.connect_signal(self)
        self.sig_add_item.connect(self.parent.add_item)
        self.sig_refresh_tree.connect(self.parent.refresh_tree)
        self.sig_save_items.connect(self.parent.save_items)
        self.sig_run_import.connect(self.parent.on_import_click)

    def before_run(self):
        self.parent.parents = {}
        self.parent.items = []

    def after_run(self):
        if self.cancel:
            self.sig_prompt.emit('素材解析中止！')
        elif not self.parent.direct_toggle.isChecked():
            self.sig_prompt.emit('素材解析完成！')
        self.sig_refresh_tree.emit()
        if self.parent.debug:
            self.sig_save_items.emit(False)
        if self.parent.direct_toggle.isChecked():
            self.sig_run_import.emit(True)


class ImportResource(Progress):
    sig_item_change_state = pyqtSignal(object, str)

    def __init__(self, parent):
        Progress.__init__(self, parent, import_resource)
        self.name = '匯入素材...'

    def connect_signal(self):
        Progress.connect_signal(self)
        self.sig_item_change_state.connect(self.parent.item_change_state)
