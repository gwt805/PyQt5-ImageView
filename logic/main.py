import darkdetect
import style.static_rc
from PyQt5.QtGui import QIcon
from .window import MainWindow
from config.config import siganl
from utils.style import load_style
from PyQt5.QtCore import Qt, QCoreApplication
from qframelesswindow import FramelessWindow, StandardTitleBar
from PyQt5.QtWidgets import QVBoxLayout, QDesktopWidget, QSystemTrayIcon, QMenu, QAction


class ImageView(FramelessWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.loadTrayMenu()
        self.center_window()
        self.set_theme(darkdetect.isDark())
        siganl.is_dark.connect(self.set_theme)
        # self.setAttribute(Qt.WA_StyledBackground, True)
        self.show()

    def setupUi(self):
        self.resize(800, 550)
        self.title_bar = StandardTitleBar(self)
        self.title_bar.setTitle("图片查看工具")
        self.title_bar.setIcon(":/image/logo.png")
        self.setTitleBar(self.title_bar)
        self.setObjectName("MainApp")

        self.main_ui = MainWindow(self)
        self.main_ui.setAttribute(Qt.WA_StyledBackground, True)
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 32, 0, 0)
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.main_ui)

    def center_window(self):
        """将窗口居中显示在屏幕上"""
        screen_geometry = QDesktopWidget().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def set_theme(self, is_dark):
        if is_dark:
            self.main_ui.theme.setCurrentIndex(0)
            self.setStyleSheet(load_style(":/theme/dark.qss"))
        else:
            self.main_ui.theme.setCurrentIndex(1)
            self.setStyleSheet(load_style(":/theme/light.qss"))

    def loadTrayMenu(self):
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon(':/image/logo.png'))
        showAction = QAction(QIcon(':/image/logo.png'), "打开应用", self, triggered = self.Show)
        quitAction = QAction(QIcon(':/image/logo.png'), "退出应用", self, triggered = lambda: QCoreApplication.instance().quit())
        self.trayMenu = QMenu(self)
        self.trayMenu.addAction(showAction)
        self.trayMenu.addSeparator()
        self.trayMenu.addAction(quitAction)
        self.tray.setContextMenu(self.trayMenu)
        self.tray.show()

    def Show(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        self.hide()
        event.ignore()