import os
from natsort import natsorted
from utils.style import load_style
from PyQt5.QtCore import QEvent, Qt
from ui.mainui import Ui_MainWindow
from PyQt5.QtGui import QIcon, QPixmap
from components.label import ScaleLabel
from config.config import config, siganl
from PyQt5.QtWidgets import QFileDialog, QTreeWidgetItem

class MainWindow(Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.icon_dict = {
            self.menu_folder: "folder.png",
            self.btn_prev: "left.png",
            self.btn_next: "right.png",
            self.btn_rotate: "rotate.png",
            self.btn_delete: "delete.png"
        }
        self.set_theme()

        self.scalelabel = ScaleLabel(self)
        self.scalelabel.hide()

        self.folder_path = ""
        self.current_path = ""
        self.image_idx = 0
        self.image_list = []

        self.splitter.setChildrenCollapsible(False)
        self.treeWidget.installEventFilter(self)

        self.graphicsView.keyPressEvent = self.keyPressEvent
        self.graphicsView.keyReleaseEvent = self.keyReleaseEvent

        self.theme.currentIndexChanged.connect(self.set_theme)
        self.graphicsView.scaleChanged.connect(self.showScale)
        self.menu_folder.clicked.connect(self.chose_folder) # 选择图片所在文件夹
        self.btn_prev.clicked.connect(lambda: self.image_option("prev")) # 上一张图片
        self.btn_next.clicked.connect(lambda: self.image_option("next")) # 下一张图片
        self.btn_delete.clicked.connect(self.delete_image) # 删除图片
        self.btn_rotate.clicked.connect(self.graphicsView.rotate_image) # 旋转图片
        self.input_idx.valueChanged.connect(self.input_idx_changed)
        self.treeWidget.itemSelectionChanged.connect(self.on_tree_item_changed) # 树形控件选择改变时触发

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

    def set_theme(self):
        if self.theme.currentText() == "暗黑":
            siganl.is_dark.emit(True)
            self.setStyleSheet(load_style(":/theme/dark.qss"))
            for k, v in self.icon_dict.items():
                icon = QIcon()
                icon.addPixmap(QPixmap(":/image/dark/" + v), QIcon.Normal, QIcon.Off)
                k.setIcon(icon)
            icon = QIcon()
            icon.addPixmap(QPixmap(":/image/dark/dark.png"), QIcon.Normal, QIcon.Off)
            self.theme.setItemIcon(0, icon)
            icon = QIcon()
            icon.addPixmap(QPixmap(":/image/dark/light.png"), QIcon.Normal, QIcon.Off)
            self.theme.setItemIcon(1, icon)
            
        if self.theme.currentText() == "浅色":
            siganl.is_dark.emit(False)
            self.setStyleSheet(load_style(":/theme/light.qss"))
            for k, v in self.icon_dict.items():
                icon = QIcon()
                icon.addPixmap(QPixmap(":/image/light/" + v), QIcon.Normal, QIcon.Off)
                k.setIcon(icon)
            icon = QIcon()
            icon.addPixmap(QPixmap(":/image/light/dark.png"), QIcon.Normal, QIcon.Off)
            self.theme.setItemIcon(0, icon)
            icon = QIcon()
            icon.addPixmap(QPixmap(":/image/light/light.png"), QIcon.Normal, QIcon.Off)
            self.theme.setItemIcon(1, icon)

    def chose_folder(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if self.folder_path:
            self.treeWidget.clear()
            # 2. 创建最顶层的根节点
            root_item = QTreeWidgetItem(self.treeWidget)
            root_item.setData(0, Qt.UserRole, self.folder_path)
            root_item.setText(0, self.folder_path)
            root_item.setIcon(0, self.style().standardIcon(getattr(self.style(), 'SP_DirIcon', 0)))
            
            # 3. 将这个根节点作为父节点，开始递归扫描其内部的子文件夹
            self.build_tree(self.folder_path, root_item)
            self.treeWidget.expandAll()
            # self.build_tree(self.folder_path, self.treeWidget.invisibleRootItem())
    
    def build_tree(self, current_path, parent_item):
        try:
            with os.scandir(current_path) as entries:
                dirs = [entry for entry in entries if entry.is_dir() and not entry.name.startswith('.')]
            
                # 2. 再对过滤后的文件夹按名称进行自然排序 (关键修复：加上 key=lambda e: e.name)
                sorted_entries = natsorted(dirs, key=lambda e: e.name)
            
                for entry in sorted_entries:
                    if entry.is_dir():
                        # 可选：过滤掉隐藏文件夹（如 .git, __pycache__ 等）
                        if entry.name.startswith('.'):
                            continue

                        # 创建树节点
                        item = QTreeWidgetItem(parent_item,)
                        item.setText(0, entry.name)
                        item.setData(0, Qt.UserRole, entry.path)
                        
                        # 设置文件夹图标（使用系统自带的图标）
                        item.setIcon(0, self.style().standardIcon(getattr(self.style(), 'SP_DirIcon', 0)))

                        # 递归扫描子文件夹
                        self.build_tree(entry.path, item)
        except PermissionError:
            # 处理无权限访问的系统文件夹（如Windows的C:\System Volume Information）
            pass
        except Exception as e:
            print(f"扫描出错 [{current_path}]: {e}")

    def on_tree_item_changed(self):
        if len(self.treeWidget.selectedItems()) > 0:
            self.current_path = self.treeWidget.selectedItems()[0].data(0, Qt.UserRole)
            self.image_idx = 0
            self.image_list = []
            self.load_image_list()
        else:
            self.label_image_idx.setText("0")
            self.label_image_total.setText("0")
            self.imgname.setText("未加载图片")
            self.input_idx.setMaximum(0)
            self.graphicsView.loadImage(None)

    def scan_images(self, path):
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_dir():
                    # 如果是目录，递归进入该目录继续查找
                    yield from self.scan_images(entry.path)
                elif entry.is_file() and entry.name.lower().endswith(config.img_suffix):
                    # 如果是图片文件，返回它的完整路径
                    yield entry.path

    def load_image_list(self):
        self.image_list = self.image_list = natsorted(self.scan_images(self.current_path))
        self.label_image_total.setText(str(len(self.image_list)))
        if self.image_list:
            self.input_idx.setMinimum(1)
            self.input_idx.setMaximum(len(self.image_list))
            self.show_image()
        else:
            self.label_image_idx.setText("0")
            self.label_image_total.setText("0")
            self.imgname.setText("未加载图片")
            self.input_idx.setMaximum(0)
            self.graphicsView.loadImage(None)

    def image_option(self, option):
        if self.image_list:
            if option == "prev":
                if self.image_idx - 1 >= 0:
                    self.image_idx -= 1

            if option == "next":
                if self.image_idx < len(self.image_list) - 1:
                    self.image_idx += 1
            self.show_image()

    def input_idx_changed(self):
        if self.image_list:
            self.image_idx = self.input_idx.value() - 1
            self.show_image()

    def delete_image(self):
        if self.image_list:
            try:
                if os.path.exists(self.image_list[self.image_idx]):
                    os.remove(self.image_list[self.image_idx])
                self.image_list.pop(self.image_idx)
                self.label_image_total.setText(str(len(self.image_list)))
                self.input_idx.setMaximum(len(self.image_list))

                if self.image_idx > len(self.image_list) - 1:
                    self.image_idx = len(self.image_list) - 1
                if len(self.image_list) == 0:
                    self.label_image_idx.setText("0")
                    self.input_idx.setMaximum(0)
                    self.imgname.setText("未加载图片")
                    self.graphicsView.loadImage(None)
                else:
                    self.show_image()
            except Exception as e:
                # self.showMsg("错误提示", f"err: {str(e)}")
                pass

    def showScale(self, scale):
        self.scalelabel.show_scale(scale)

    def show_image(self):
        if self.image_list:
            self.status_bar_folder_value.setText(self.image_list[self.image_idx])
            self.label_image_idx.setText(str(self.image_idx + 1))
            self.imgname.setText(os.path.split(self.image_list[self.image_idx])[-1])
            self.label_image_total.setText(str(len(self.image_list)))
            self.graphicsView.loadImage(self.image_list[self.image_idx])
        else:
            self.status_bar_folder_value.setText("未加载图片")

    def eventFilter(self, obj, event):
        if obj is self.treeWidget:
            # 判断事件类型是不是键盘按下或释放
            if event.type() == QEvent.KeyPress:
                # 返回 True 表示事件已被处理，阻止它继续向下传递
                if event.key() == Qt.Key.Key_Left:
                    if self.image_list:
                        self.btn_prev.setDown(True)
                        self.image_option("prev")
                if event.key() == Qt.Key.Key_Right:
                    if self.image_list:
                        self.btn_next.setDown(True)
                        self.image_option("next")
                if event.key() == Qt.Key.Key_Delete:
                    if self.image_list:
                        self.btn_delete.setDown(True)
                        self.delete_image()
                if event.key() == Qt.Key.Key_R:
                    if self.image_list:
                        self.btn_rotate.setDown(True)
                        self.graphicsView.rotate_image()
                return True
            if event.type() == QEvent.KeyRelease:
                if event.key() == Qt.Key.Key_Left:
                    if self.image_list:
                        self.btn_prev.setDown(False)
                if event.key() == Qt.Key.Key_Right:
                    if self.image_list:
                        self.btn_next.setDown(False)
                if event.key() == Qt.Key.Key_Delete:
                    if self.image_list:
                        self.btn_delete.setDown(False)
                if event.key() == Qt.Key.Key_R:
                    if self.image_list:
                        self.btn_rotate.setDown(False)
                return True
        # 如果不是我们关心的对象或事件类型，返回 False 让事件继续传递
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.btn_prev.setDown(True)
            self.image_option("prev")
        elif event.key() == Qt.Key.Key_Right:
            self.btn_next.setDown(True)
            self.image_option("next")
        elif event.key() == Qt.Key.Key_Delete:
            self.btn_delete.setDown(True)
            self.delete_image()
        elif event.key() == Qt.Key.Key_R:
            self.btn_rotate.setDown(True)
            self.graphicsView.rotate_image()
    
    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.btn_prev.setDown(False)
        elif event.key() == Qt.Key.Key_Right:
            self.btn_next.setDown(False)
        elif event.key() == Qt.Key.Key_Delete:
            self.btn_delete.setDown(False)
        elif event.key() == Qt.Key.Key_R:
            self.btn_rotate.setDown(False)

    def resizeEvent(self, event):
        self.scalelabel.moveCenter()

