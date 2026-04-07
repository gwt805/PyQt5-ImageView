import sys
from PyQt5.QtCore import Qt
from logic.main import ImageView
from PyQt5.QtWidgets import QApplication, QMessageBox

def main():
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        app = QApplication(sys.argv)
        window = ImageView()
        sys.exit(app.exec_())
    except Exception as e:
        reply = QMessageBox(QMessageBox.Warning, "警告", str(e), QMessageBox.NoButton)
        reply.addButton("确定", QMessageBox.YesRole)
        reply.addButton("取消", QMessageBox.NoRole)
        reply.exec_()

if __name__ == '__main__':
    main()