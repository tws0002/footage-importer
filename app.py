from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.main import FootageImporter
import sys
import os


os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
app = QApplication(sys.argv)
app.setAttribute(Qt.AA_EnableHighDpiScaling)

window = FootageImporter(debug=False)
window.show()

sys.exit(app.exec_())
