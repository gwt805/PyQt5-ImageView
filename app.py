import os, sys
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from natsort import natsorted
from mainui import Ui_MainWindow
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtGui import  QPixmap, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QFileDialog, QGraphicsPixmapItem, QMessageBox

class AppImageView(Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.image_extensions = ('.png', '.jpg', '.jpeg', '.svg', '.webp', '.ico', '.icon', '.gif', '.bmp', '.tiff')
        self.action_dir.triggered.connect(self.get_imgs)
        self.img_idx = 0
        self.img_list = []
        self.btn_prev.clicked.connect(lambda: self.image_option("prev"))
        self.btn_next.clicked.connect(lambda: self.image_option("next"))
        self.btn_xuanzhuan.clicked.connect(self.rotate_img)
        self.img_idx_input.textChanged.connect(self.input_img_idx)
        self.label = QtWidgets.QLabel()
        self.statusBar().addWidget(self.label)
        self.model = QStandardItemModel()

        self.show()
    
    def get_imgs(self):
        self.path = QFileDialog.getExistingDirectory(self, "选择图片所在文件夹")
        if self.path:
            self.remove_params()
            self.label.setText(f"当前目录: {self.path}")
            self.img_list = self.find_image_files()
            self.img_list = natsorted(self.img_list)
            if self.img_list:
                self.img_idx_now.setText("1")
                self.img_idx_total.setText(str(len(self.img_list)))
            self.img_list_show()
            self.img_show("first")

    def find_image_files(self):
        image_files = []
        for root, dirs, files in os.walk(self.path):
            for file in files:
                if file.lower().endswith(self.image_extensions):
                    image_files.append(os.path.join(root, file))
        return image_files

    def img_list_show(self):
        for it in self.img_list:
            item = QStandardItem(it)
            item.setToolTip(it)
            self.model.appendRow(item)
        self.listView.setModel(self.model)
        self.listView.selectionModel().selectionChanged.connect(self.img_list_select)

    def input_img_idx(self):
        if self.img_idx_input.value() <= 0:
            self.img_idx_input.setValue(1)
            self.img_idx_now.setText("1")
            self.img_idx = 0
        elif self.img_idx_input.value() > len(self.img_list):
            self.img_idx_input.setValue(len(self.img_list))
            self.img_idx_now.setText(str(len(self.img_list)))
            self.img_idx = len(self.img_list) - 1
        else:
            self.img_idx = int(self.img_idx_input.text()) - 1
            self.img_show("update")

    def img_list_select(self, selected, deselected):
        if selected.indexes():
            self.img_idx = selected.indexes()[0].row()
            self.img_idx_now.setText(str(self.img_idx + 1))
            self.img_show("update")

    def img_show(self, option):
        if self.img_list:
            self.listView.setCurrentIndex(self.model.index(self.img_idx, 0))
            try:
                self.img_name.setText(f" {self.img_list[self.img_idx]} ")
                self.img_idx_now.setText(str(self.img_idx + 1))
                frame = QPixmap(self.img_list[self.img_idx])
                self.graphicsView.image = frame
                self.graphicsView.image_item = QGraphicsPixmapItem(frame)
                if option == "first":
                    self.graphicsView.loadImage()
                if option == "update":
                    self.graphicsView.update_image()
            except Exception as e:
                self.showMsg("错误提示", f"err: {str(e)}")
        else:
            self.img_name.setText("未找到图片")
            self.graphicsView.scene.clear()
            self.graphicsView.image_item = None
            return None

    def rotate_img(self):
        if self.img_list:
            self.graphicsView.rotate_image()

    def image_option(self, option: str):
        if self.img_list:
            if option == "prev":
                if self.img_idx - 1 >= 0:
                    self.img_idx -= 1

            if option == "next":
                if self.img_idx < len(self.img_list) - 1:
                    self.img_idx += 1
            self.img_show("update")

    def remove_params(self):
        self.img_idx = 0
        self.img_list = []
        self.img_idx_now.setText("0")
        self.img_idx_total.setText("0")
        self.img_idx_input.clear()
        self.img_name.setText("未找到图片")
        self.graphicsView.scene.clear()
        self.graphicsView.image_item = None
        self.model.clear()

    def showMsg(self, title: str, msg: str):
        reply = QMessageBox(QMessageBox.Warning, title, msg, QMessageBox.NoButton, self)
        reply.addButton("确定", QMessageBox.YesRole)
        reply.addButton("取消", QMessageBox.NoRole)
        reply.exec_()

def main():
    QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QtWidgets.QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QtWidgets.QApplication(sys.argv)
    server_name = "pyqt5-image-viewer"
    socket = QLocalSocket()
    
    socket.connectToServer(server_name)
    if socket.waitForConnected(1000):
        app.quit()
    else:
        local_server = QLocalServer()
        local_server.listen(server_name)
        app.setQuitOnLastWindowClosed(False)
        aiv = AppImageView()
        sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"err: {str(e)}")