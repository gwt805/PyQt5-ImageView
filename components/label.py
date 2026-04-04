import style.static_rc
from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QColor, QFont, QPainter, QPainterPath

class ElidedLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._elide_mode = QtCore.Qt.ElideRight
        self._full_text = ""
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)

    def setText(self, text: str):
        # 永远保存完整内容
        self._full_text = text
        self.update_elided_text()

    def text(self) -> str:
        # 返回完整文本，而不是省略的
        return self._full_text

    def setElideMode(self, mode):
        self._elide_mode = mode
        self.update_elided_text()

    def update_elided_text(self):
        fm = QtGui.QFontMetrics(self.font())
        available_width = max(0, self.width() - self.contentsMargins().left() - self.contentsMargins().right())
        elided = fm.elidedText(self._full_text, self._elide_mode, available_width)
        super().setText(elided)

        # 🚀 判断是否被省略，设置 tooltip
        if elided != self._full_text:
            self.setToolTip(self._full_text)
        else:
            self.setToolTip("")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_elided_text()


class ScaleLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setFixedSize(60, 30)
        self.moveCenter()
        self.setStyleSheet("background-color: transparent;")

    def moveCenter(self):
        self.move((self.parent().width() - self.width()) // 2, (self.parent().height() - self.height()) // 2)

    def show_scale(self, scale_value: int):
        self._scale = int(scale_value * 100)
        # 判断是否可见
        if not self.isVisible():
            self.show()
            QTimer.singleShot(2000, self.hide_scale)

    def hide_scale(self):
        """ 隐藏缩放比例标签 """
        self.hide()

    def getFont(self, fontSize=14, weight=QFont.Normal,fontType: str = 'Microsoft YaHei'):
        font = QFont()
        font.setFamilies(['Segoe UI', fontType, 'PingFang SC'])
        font.setPixelSize(fontSize)
        font.setWeight(weight)
        return font

    def paintEvent(self, e):
        """ 绘制事件处理 """
        painter = QPainter(self)
        painter.setRenderHints(QPainter.TextAntialiasing | QPainter.HighQualityAntialiasing | QPainter.SmoothPixmapTransform)
        rectf = QRectF(self.rect()) 
        rounded_rect = QPainterPath() # 创建圆角矩形路径
        rounded_rect.addRoundedRect(rectf, 13, 13)
        painter.setBrush(QColor(0, 0, 0, 90))
        painter.setPen(Qt.NoPen)
        painter.drawPath(rounded_rect)
        painter.setPen(QColor(255, 255, 255))
        rectf.adjust(5,1,-1,-1)
        painter.setFont(self.getFont(12, QFont.ExtraBold))
        painter.drawText(rectf, Qt.AlignCenter, f"{self._scale}%")