from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QTreeWidget

class NoKeyTreeWidget(QTreeWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

    def keyPressEvent(self, event: QKeyEvent):
        pass