from PyQt5.QtCore import QObject, pyqtSignal

class Signal(QObject):
    is_dark = pyqtSignal(bool)

siganl = Signal()


class Config(QObject):
    def __init__(self):
        self.img_suffix = (".jpg", ".png", ".jpeg", ".bmp", ".gif", ".tiff", ".webp", ".svg", ".ico", ".heic", ".heif")

config = Config()