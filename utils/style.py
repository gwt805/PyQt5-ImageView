from PyQt5.QtCore import QFile, QTextStream

def load_style(style_file: str):
    file = QFile(style_file)
    if not file.open(QFile.ReadOnly | QFile.Text):
        return None
    stream = QTextStream(file)
    return stream.readAll()
