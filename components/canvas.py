import os, uuid, json
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF, QLineF
from PyQt5.QtGui import QPainter, QPixmap, QWheelEvent, QMouseEvent, QTransform, QPainter, QPen, QBrush, QColor, QPolygonF
from PyQt5.QtWidgets import  QAction, QApplication, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QGraphicsWidget, QGraphicsRectItem, QGraphicsPolygonItem, QMenu

class CanvasQG(QGraphicsView):
    scaleChanged = pyqtSignal(float)
    def __init__(self, parent=None):
        super().__init__()
        self.setParent(parent)
        self.image_item = None
        self.current_angle = 0
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def get_fit_scale(self):
        if not self.image_item:
            return 1.0
        view_rect = self.viewport().rect()
        scene_rect = self.image_item.boundingRect()
        if scene_rect.width() == 0 or scene_rect.height() == 0:
            return 1.0
        scale_x = view_rect.width() / scene_rect.width()
        scale_y = view_rect.height() / scene_rect.height()
        return min(scale_x, scale_y)

    def loadImage(self, image: QPixmap):
        if self.image_item:
            self.scene.clear()
        image = QPixmap(image)
        self.image_item = QGraphicsPixmapItem(image)
        self.image_item.setFlag(QGraphicsPixmapItem.ItemIsMovable)
        self.image_item.setTransformationMode(Qt.SmoothTransformation)
        self.scene.addItem(self.image_item)
        self.fitInView(self.image_item, Qt.KeepAspectRatio)
        self.center_image()
        self.show()

    def wheelEvent(self, event: QWheelEvent):
        if self.image_item:
            current_scale = self.transform().m11()
            delta = event.angleDelta().y()
            scale_factor = 1.1 if delta > 0 else 0.9

            new_scale = current_scale * scale_factor
            new_scale = max(0.1, min(new_scale, 5.0))

            if new_scale == current_scale: return

            old_pos_view = event.pos()
            old_pos_scene = self.mapToScene(old_pos_view)
            self.scale(new_scale / current_scale, new_scale / current_scale)
            new_pos_view = self.mapFromScene(old_pos_scene)
            offset = new_pos_view - old_pos_view
            self.translate(offset.x(), offset.y())
            self.scaleChanged.emit(new_scale)

    def rotate_image(self):
        if self.image_item:
            # self.current_angle += 90
            # self.image_item.setRotation(self.current_angle)
            # bounding_rect = self.image_item.boundingRect()
            # self.image_item.setTransformOriginPoint(bounding_rect.center())
            # self.center_image()
            # if self.current_angle >= 360:
            #     self.current_angle = 0
            self.current_angle += 90
            self.image_item.setRotation(self.current_angle)
            bounding_rect = self.image_item.boundingRect()
            self.image_item.setTransformOriginPoint(bounding_rect.center())
            self.center_image()
            if self.current_angle >= 360:
                self.current_angle = 0
            self.fitInView(self.image_item, Qt.KeepAspectRatio)
            self.scaleChanged.emit(self.transform().m11())

    def center_image(self):
        if self.image_item:
            view_center = self.viewport().rect().center()
            scene_center = self.mapToScene(view_center)
            self.image_item.setPos(scene_center - self.image_item.boundingRect().center())

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        copy_action = QAction("复制图片", self)
        copy_action.triggered.connect(self.copy_image_to_clipboard)
        context_menu.addAction(copy_action)
        context_menu.exec_(event.globalPos())

    def copy_image_to_clipboard(self):
        if self.image_item:
            pixmap = self.image_item.pixmap()
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image_item:
            self.fitInView(self.image_item, Qt.KeepAspectRatio)
            self.scaleChanged.emit(self.get_fit_scale())
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if self.image_item:
            self.fitInView(self.image_item, Qt.KeepAspectRatio)
            self.current_angle = 0
            self.image_item.setRotation(self.current_angle)
            self.center_image()
            self.scaleChanged.emit(self.get_fit_scale())

class CanvasQGANNO(CanvasQG):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.key_pressed_alt = False
        self.setDragMode(QGraphicsView.NoDrag)
        # 标注配置
        self.current_label = 'person' # 当前选中的标签
        self.current_label_color = {
            "person": QColor(255,255,0),
            "car": QColor(0,255,0),
            "tree": QColor(0,0,255)
        } # 标签对应标注框的颜色
        self.current_image_name = None # 当前图像的文件名
        self.save_path = r'D:\Data\test' # 保存标注的路径
        # 标注相关
        self.is_drawing = False
        self.draw_mode = None # 绘制模式, 矩形框、多边形、点
        self.draw_last_mode = None # 上一次的绘制模式
        self.show_crosshair = False
        self.rect_start_pos = None # 矩形框的起始位置, 现在存储相对于图片的局部坐标
        self.current_pos = None # 矩形框的当前点, 现在存储相对于图片的局部坐标
        self.selected_item = None # 当前选中的标注项
        self.anno_items = []
        self.anno_tmp_pos = []
        # 编辑相关
        self.is_editing = False # 是否处于编辑状态
        self.editing_item = None # 当前正在编辑的item
        self.edit_mode = None # 编辑模式: rect, polygon, point
        self.dragged_vertex_index = None # 对于多边形，记录拖动的顶点索引
        self.drag_start_pos = None # 编辑开始时的鼠标位置
        self.drag_start_vertex_pos_local = None # 编辑开始时，被拖动顶点的本地坐标

    def loadImage(self, image):
        self.anno_items = []
        super().loadImage(image)
        self.restore_annotations()
        self.update()

    # ---------- 绘制标注项 ----------
    def _create_rect_item(self, rect):
        """创建矩形标注"""
        rect_item = QGraphicsRectItem(rect)
        rect_item.setParentItem(self.image_widget)
        rect_item.setPen(QPen(self.current_label_color.get(self.current_label, QColor(255,0,0)), 1))
        rect_item.setBrush(QBrush(Qt.NoBrush))
        rect_item.anno_data = {
            "image": self.current_image_name,
            "id": str(uuid.uuid4()),
            "type": "rect",
            "label": self.current_label,
            "points": [rect.topLeft(), rect.bottomRight()]
        }
        self.anno_items.append(rect_item)

    def _create_polygon_item(self, polygon_points):
        """创建多边形标注"""
        qpolygon = QPolygonF(polygon_points)
        polygon_item = QGraphicsPolygonItem(qpolygon)
        polygon_item.setParentItem(self.image_widget)
        polygon_item.setPen(QPen(self.current_label_color.get(self.current_label, QColor(255,0,0)), 1))
        polygon_item.setBrush(QBrush(Qt.NoBrush))
        polygon_item.anno_data = {
            "image": self.current_image_name,
            "id": str(uuid.uuid4()),
            "type": "polygon",
            "label": self.current_label,
            "points": [(p.x(), p.y()) for p in polygon_points]
        }
        self.anno_items.append(polygon_item)

    def _update_rect_anno(self, item):
        rect = item.rect()
        item.anno_data["points"] = [
            (rect.topLeft().x(), rect.topLeft().y()),
            (rect.topRight().x(), rect.topRight().y()),
            (rect.bottomRight().x(), rect.bottomRight().y()),
            (rect.bottomLeft().x(), rect.bottomLeft().y())
        ]

    def _update_polygon_anno(self, item):
        polygon = item.polygon()
        item.anno_data["points"] = [(p.x(), p.y()) for p in polygon]


    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if not self.image_widget: return
        if event.button() == Qt.LeftButton and self.selected_item and not self.is_drawing:
            clicked_vertex_index = self._get_vertex_at_pos(self.selected_item, event.pos())
            if clicked_vertex_index is not None:  # 拖动顶点
                self.is_editing = True
                self.editing_item = self.selected_item
                self.edit_mode = 'resize_rect' if isinstance(self.editing_item, QGraphicsRectItem) else 'move_polygon_vertex'
                self.dragged_vertex_index = clicked_vertex_index
                self.drag_start_pos = event.pos()
                if isinstance(self.editing_item, QGraphicsRectItem):
                    rect = self.editing_item.rect()
                    corners = [rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()]
                    self.drag_start_vertex_pos_local = corners[clicked_vertex_index]
                elif isinstance(self.editing_item, QGraphicsPolygonItem):
                    polygon = self.editing_item.polygon()
                    self.drag_start_vertex_pos_local = polygon.at(clicked_vertex_index)
                self.setCursor(Qt.ClosedHandCursor)
                self.update()
                return

            # 如果点击矩形内部而不是顶点 → 移动整个矩形
            if isinstance(self.selected_item, QGraphicsRectItem):
                rect = self.selected_item.rect()
                # 把点击位置映射到矩形局部坐标
                scene_pos = self.mapToScene(event.pos())
                local_pos = self.selected_item.mapFromScene(scene_pos)
                if rect.contains(local_pos):
                    self.is_editing = True
                    self.editing_item = self.selected_item
                    self.edit_mode = 'move_item'
                    self.drag_start_pos = event.pos()
                    self.setCursor(Qt.ClosedHandCursor)
                    self.update()
                    return
        if event.button() == Qt.LeftButton and self.key_pressed_alt:
            self.image_widget.setFlag(QGraphicsWidget.ItemIsMovable, True)
            self.last_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.LeftButton and self.is_drawing and self.draw_mode == 'rect':
            scene_pos = self.mapToScene(event.pos())
            local_pos = self.image_widget.mapFromScene(scene_pos)
            self.rect_start_pos = local_pos
            if len(self.anno_tmp_pos) < 2:
                self.anno_tmp_pos.append(self.rect_start_pos)
                self.current_pos = self.rect_start_pos
            self.update()
        elif event.button() == Qt.LeftButton and self.is_drawing and self.draw_mode == 'polygon':
            scene_pos = self.mapToScene(event.pos())
            local_pos = self.image_widget.mapFromScene(scene_pos)
            self.anno_tmp_pos.append(local_pos)
            self.current_pos = local_pos
            self.update()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if not self.image_widget: return
        if event.button() == Qt.LeftButton and self.is_editing: # 结束编辑模式
            self.is_editing = False
            self.editing_item = None
            self.edit_mode = None
            self.dragged_vertex_index = None
            self.drag_start_pos = None
            self.drag_start_vertex_pos_local = None
            self.setCursor(Qt.ArrowCursor)
            self.update()
            return
        if event.button() == Qt.LeftButton and self.key_pressed_alt:
            self.image_widget.setFlag(QGraphicsWidget.ItemIsMovable, False)
            self.setCursor(Qt.ArrowCursor)
        elif event.button() == Qt.LeftButton and self.is_drawing and self.draw_mode == 'rect':
            if len(self.anno_tmp_pos) == 2:
                rect = QRectF(self.anno_tmp_pos[0], self.anno_tmp_pos[1]).normalized()
                clipped_rect = self.clip_rect_to_image(rect) # 裁剪矩形框到图片范围内
                if clipped_rect.isValid():
                    self._create_rect_item(clipped_rect)
                    self.save_annotations()
                # 清空临时变量
                self.anno_tmp_pos = []
                self.rect_start_pos = None
                self.current_pos = None
                self.draw_mode = None
                self.setCursor(Qt.ArrowCursor)
                self.is_drawing = False
                self.update()
                
    def mouseMoveEvent(self, event):
        if not self.image_widget: return
        if self.is_editing:
            # 1. 获取鼠标在场景中的位置
            current_scene_pos = self.mapToScene(event.pos())
            # 2. 获取鼠标在正在编辑的Item的本地坐标
            new_pos_local = self.editing_item.mapFromScene(current_scene_pos)

            # --- 核心修复：在正确的坐标系中进行裁剪 ---
            # 3. 将点的本地坐标 转换到 图片的本地坐标
            new_pos_in_image_coords = self.image_widget.mapFromItem(self.editing_item, new_pos_local)
            
            # 4. 在图片的本地坐标中进行裁剪
            clipped_pos_in_image_coords = self.clip_point_to_image(new_pos_in_image_coords)
            
            # 5. 将裁剪后的点转换回 Item的本地坐标
            final_pos_local = self.image_widget.mapToItem(self.editing_item, clipped_pos_in_image_coords)

            scene_pos = self.mapToScene(event.pos())
            if self.edit_mode == 'move_item':
                # 计算鼠标在图片坐标系中的偏移量
                start_pos_in_image = self.image_widget.mapFromScene(self.mapToScene(self.drag_start_pos))
                current_pos_in_image = self.image_widget.mapFromScene(self.mapToScene(event.pos()))
                delta_in_image = current_pos_in_image - start_pos_in_image

                # 计算新的位置
                new_item_pos = self.drag_start_vertex_pos_local + delta_in_image
                
                # --- 边界约束：确保整个Item都在图片内 ---
                item_rect = self.editing_item.boundingRect()
                image_rect = self.image_widget.boundingRect()
                
                # 计算允许的x和y范围
                min_x = image_rect.left()
                max_x = image_rect.right() - item_rect.width()
                min_y = image_rect.top()
                max_y = image_rect.bottom() - item_rect.height()
                
                # 应用约束
                final_x = max(min_x, min(new_item_pos.x(), max_x))
                final_y = max(min_y, min(new_item_pos.y(), max_y))
                
                self.editing_item.setPos(QPointF(final_x, final_y))
                self._update_rect_anno(self.editing_item)
                self.update()
                self.save_annotations()
            elif self.edit_mode == 'resize_rect' and isinstance(self.editing_item, QGraphicsRectItem):
                # 拖动角点
                rect = self.editing_item.rect()
                corners = [rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()]
                opposite_corner_local = corners[(self.dragged_vertex_index + 2) % 4]

                # 把鼠标位置裁剪到图片范围
                local_pos = self.editing_item.mapFromScene(scene_pos)
                new_pos_in_image = self.image_widget.mapFromItem(self.editing_item, local_pos)
                clipped_pos = self.clip_point_to_image(new_pos_in_image)
                final_pos_local = self.image_widget.mapToItem(self.editing_item, clipped_pos)

                new_rect = QRectF(final_pos_local, opposite_corner_local).normalized()
                self.editing_item.setRect(new_rect)
                self._update_rect_anno(self.editing_item)
                self.update()
                self.save_annotations()
            elif self.edit_mode == 'move_rect' and isinstance(self.editing_item, QGraphicsRectItem):
                # 使用 scene 坐标计算 delta
                old_scene_pos = self.mapToScene(self.drag_start_pos)
                new_scene_pos = self.mapToScene(event.pos())

                delta_scene = new_scene_pos - old_scene_pos
                self.drag_start_pos = event.pos()

                # 按 delta_scene 移动 item
                self.editing_item.moveBy(delta_scene.x(), delta_scene.y())

                # 再做边界裁剪
                rect = self.editing_item.rect()
                top_left = self.clip_point_to_image(self.editing_item.mapToParent(rect.topLeft()))
                bottom_right = self.clip_point_to_image(self.editing_item.mapToParent(rect.bottomRight()))
                self.editing_item.setRect(QRectF(self.editing_item.mapFromParent(top_left), self.editing_item.mapFromParent(bottom_right)))
                self._update_rect_anno(self.editing_item)
                self.update()
                self.save_annotations()
            elif self.edit_mode == 'move_polygon_vertex':
                # 防御性检查
                if self.dragged_vertex_index is None:
                    return
                # 更新多边形
                polygon = self.editing_item.polygon()
                polygon[self.dragged_vertex_index] = final_pos_local
                self.editing_item.setPolygon(polygon)
                self._update_polygon_anno(self.editing_item)

            self.update()
            self.save_annotations()
            return # 编辑模式下，事件处理完毕
        if self.is_drawing and self.draw_mode == 'rect':
            scene_pos = self.mapToScene(event.pos())
            self.current_pos = self.image_widget.mapFromScene(scene_pos)
            self.update()
        elif self.is_drawing and self.draw_mode == 'polygon':
            scene_pos = self.mapToScene(event.pos())
            self.current_pos = self.image_widget.mapFromScene(scene_pos)
            self.update()

        if not self.is_drawing:
            scene_pos = self.mapToScene(event.pos())
            item_at_cursor = self.scene.itemAt(scene_pos, QTransform())
            # 检查这个item是否是我们的标注项之一
            new_hovered_item = None
            if item_at_cursor and item_at_cursor in self.anno_items:
                new_hovered_item = item_at_cursor

            # 如果悬停项发生了变化，则更新状态并重绘
            if new_hovered_item != self.selected_item:
                self.selected_item = new_hovered_item
                self.update() # 触发paintEvent来绘制或清除角点

        if self.show_crosshair:
            self.crosshair_pos = self.mapToScene(event.pos())
            self.update()
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        if not self.image_widget: return
        if event.key() == Qt.Key_Alt:
            self.key_pressed_alt = True
            self.setCursor(Qt.OpenHandCursor)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if not self.image_widget: return
        if event.key() == Qt.Key_Alt:
            self.key_pressed_alt = False
            self.dragging = False
            self.is_drawing = False
            self.image_widget.setFlag(QGraphicsWidget.ItemIsMovable, False)
            self.setCursor(Qt.ArrowCursor)
        elif event.key() == Qt.Key_R and event.modifiers() & Qt.ControlModifier:
            self.draw_mode = 'rect'
            self.draw_last_mode = 'rect'
            self.setCursor(Qt.CrossCursor)
            self.is_drawing = True
        elif event.key() == Qt.Key_N and event.modifiers() & Qt.ControlModifier:
            self.draw_mode = 'polygon'
            self.draw_last_mode = 'polygon'
            self.is_drawing = True
            self.setCursor(Qt.CrossCursor)
        elif event.key() == Qt.Key_P and event.modifiers() & Qt.ControlModifier:
            self.draw_mode = 'point'
            self.draw_last_mode = 'point'
        elif event.key() == Qt.Key_N:
            if self.draw_mode == None:
                if self.draw_last_mode == None:
                    self.draw_mode = 'rect'
                else:
                    self.draw_mode = self.draw_last_mode
            self.setCursor(Qt.CrossCursor)
            self.is_drawing = True
        elif event.key() == Qt.Key_Escape:
            self.is_drawing = False
            self.anno_tmp_pos = []
            self.rect_start_pos = None
            self.current_pos = None
            self.draw_mode = None
            self.update()
        elif event.key() == Qt.Key_Delete:
            if self.selected_item:
                self.scene.removeItem(self.selected_item)
                if self.selected_item in self.anno_items:
                    self.anno_items.remove(self.selected_item)
                self.selected_item = None
                self.update()
        elif event.key() == Qt.Key_Q:
            # 结束多边形绘制
            if self.is_drawing and self.draw_mode == 'polygon':
                if len(self.anno_tmp_pos) > 2:
                    self.current_pos = self.anno_tmp_pos[-1]
                    clipped_polygon = self.clip_polygon_to_image(self.anno_tmp_pos) # 裁剪多边形到图片范围内
                    if clipped_polygon:
                        self._create_polygon_item(clipped_polygon)
                        self.save_annotations()
                    # 清空临时变量
                    self.is_drawing = False
                    self.draw_mode = None
                    self.anno_tmp_pos = []
                    self.current_pos = None
                    self.setCursor(Qt.ArrowCursor)
                    self.update()
                else:
                    self.is_drawing = False
                    self.draw_mode = None
                    self.anno_tmp_pos = []
                    self.current_pos = None
                    self.setCursor(Qt.ArrowCursor)
                    self.update()
                
        
        super().keyReleaseEvent(event)

    def paintEvent(self, event):
        if not self.image_widget: return
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        painter.save()
        if self.show_crosshair and hasattr(self, 'crosshair_pos'):
            painter.setPen(QPen(QColor(self.current_label_color[self.current_label]), 1, Qt.SolidLine))
            view_pos = self.mapFromScene(self.crosshair_pos)
            painter.drawLine(0, view_pos.y(), self.width(), view_pos.y())
            painter.drawLine(view_pos.x(), 0, view_pos.x(), self.height())
            painter.setBrush(Qt.red) # 绘制中心点
            painter.drawEllipse(view_pos, 3, 3)
        # 绘制当前正在绘制的矩形
        if self.is_drawing and self.rect_start_pos and self.current_pos:
            painter.setPen(QPen(QColor(self.current_label_color[self.current_label]), 1, Qt.SolidLine))
            scene_start_pos = self.image_widget.mapToScene(self.rect_start_pos)
            scene_current_pos = self.image_widget.mapToScene(self.current_pos)
            view_start_pos = self.mapFromScene(scene_start_pos)
            view_current_pos = self.mapFromScene(scene_current_pos)
            painter.drawRect(QRectF(view_start_pos, view_current_pos).normalized())
            painter.drawEllipse(view_start_pos, 3, 3)
            painter.drawEllipse(view_current_pos, 3, 3)
            painter.drawEllipse(QPointF(view_current_pos.x(), view_start_pos.y()), 3, 3)
            painter.drawEllipse(QPointF(view_start_pos.x(), view_current_pos.y()), 3, 3)

        # 绘制临时多边形
        if self.is_drawing and self.draw_mode == 'polygon' and self.anno_tmp_pos:
            painter.setPen(QPen(QColor(self.current_label_color[self.current_label]), 1, Qt.SolidLine))
            for i in range(len(self.anno_tmp_pos) - 1):
                # 正确的坐标转换
                scene_start = self.image_widget.mapToScene(self.anno_tmp_pos[i])
                scene_end = self.image_widget.mapToScene(self.anno_tmp_pos[i + 1])
                view_start = self.mapFromScene(scene_start)
                view_end = self.mapFromScene(scene_end)
                
                painter.drawEllipse(view_start, 3, 3)
                painter.drawLine(view_start, view_end)
                painter.drawEllipse(view_end, 3, 3)
            # 绘制最后一条线到当前鼠标位置
            scene_last = self.image_widget.mapToScene(self.anno_tmp_pos[-1])
            scene_current = self.image_widget.mapToScene(self.current_pos)
            view_last = self.mapFromScene(scene_last)
            view_current = self.mapFromScene(scene_current)
            painter.drawLine(view_last, view_current)

        # 绘制悬停项的角点
        if self.selected_item and not self.is_drawing:
            # 设置角点的样式
            painter.setPen(QPen(QColor(0, 255, 0), 2)) # 绿色边框
            painter.setBrush(QBrush(QColor(0, 255, 0, 128))) # 半透明绿色填充
            
            corner_points = []
            text = getattr(self.selected_item, 'anno_data', {}).get('label', '未知标签')
            font_metrics = painter.fontMetrics()
            text_width = font_metrics.horizontalAdvance(text)
            text_height = font_metrics.height()

            if isinstance(self.selected_item, QGraphicsRectItem):
                rect = self.selected_item.rect()
                # 展示标签
                scene_center = self.selected_item.mapToScene(rect.center())
                view_center = self.mapFromScene(scene_center)
                text_pos = view_center - QPointF(text_width / 2, text_height / 2)
                painter.drawText(text_pos, text)

                corner_points = [rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()]
            elif isinstance(self.selected_item, QGraphicsPolygonItem):
                polygon = self.selected_item.polygon()
                if polygon.count() > 0:
                    sum_x = sum(p.x() for p in polygon)
                    sum_y = sum(p.y() for p in polygon)
                    center_point = QPointF(sum_x / polygon.count(), sum_y / polygon.count())
                    scene_center = self.selected_item.mapToScene(center_point)
                    view_center = self.mapFromScene(scene_center)
                    text_pos = view_center - QPointF(text_width / 2, text_height / 2)
                    painter.drawText(text_pos, text)
                corner_points = [polygon.at(i) for i in range(polygon.count())]

            # 转换坐标并绘制
            for point in corner_points:
                # 坐标转换：Item -> Scene -> View
                scene_point = self.selected_item.mapToScene(point)
                view_point = self.mapFromScene(scene_point)
                # 绘制一个小圆点作为角点
                painter.drawEllipse(QRectF(view_point.x() - 4, view_point.y() - 4, 8, 8))
        painter.restore()

    def save_annotations(self):
        """保存标注数据"""
        anno_list = []
        for item in self.anno_items:
            data = item.anno_data.copy()
            if data['type'] == 'rect':
                data['points'] = [(p.x(), p.y()) if hasattr(p, 'x') else (p[0], p[1]) for p in data['points']]
            elif data['type'] == 'polygon':
                data['points'] = [(p[0], p[1]) for p in data['points']]
            anno_list.append(data)

        path = os.path.join(self.save_path ,f"{self.current_image_name}.json")
        if anno_list:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(anno_list, f, ensure_ascii=False, indent=4)
        else:
            if os.path.exists(path):
                os.remove(path)

    def restore_annotations(self):
        """恢复标注数据"""
        path = os.path.join(self.save_path ,f"{self.current_image_name}.json")
        if not os.path.exists(path):
            return

        with open(path, 'r', encoding='utf-8') as f:
            anno_list = json.load(f)
        for data in anno_list:
            if data['type'] == 'rect':
                item = self.add_rect(data['points'], data['label'])
            elif data['type'] == 'polygon':
                item = self.add_polygon(data['points'], data['label'])
            item.anno_data = data

    def add_rect(self, points, label):
        """添加矩形"""
        rect = QRectF(QPointF(points[0][0], points[0][1]), QPointF(points[2][0], points[2][1]))
        item = QGraphicsRectItem(rect)
        item.setBrush(QBrush(Qt.NoBrush))
        item.setPen(QPen(self.current_label_color.get(label, QColor(255,0,0)), 1))
        item.anno_data = {'type': 'rect', 'points': points, 'label': label} # 添加标注数据
        self.anno_items.append(item)
        self.addItem(item)
        return item

    def add_polygon(self, points, label):
        """添加多边形"""
        polygon = QPolygonF([QPointF(p[0], p[1]) for p in points])
        item = QGraphicsPolygonItem(polygon)
        item.setBrush(QBrush(Qt.NoBrush))
        item.setPen(QPen(self.current_label_color.get(label, QColor(255,0,0)), 1))
        item.anno_data = {'type': 'polygon', 'points': points, 'label': label} # 添加标注数据
        self.anno_items.append(item)
        self.addItem(item)
        return item
                

    def clip_rect_to_image(self, rect):
        """将矩形裁剪到图片边界内"""
        if not self.image_widget:
            return rect
            
        # 获取图片的边界矩形
        image_rect = self.image_widget.boundingRect()
        
        # 确保矩形在图片边界内
        clipped_rect = rect.intersected(image_rect)
        
        return clipped_rect

    def clip_point_to_image(self, point):
        """将点裁剪到图片边界内"""
        if not self.image_widget:
            return point
            
        # 获取图片的边界矩形
        image_rect = self.image_widget.boundingRect()
        
        # 确保点在图片边界内
        clipped_point = QPointF(
            max(image_rect.left(), min(point.x(), image_rect.right())),
            max(image_rect.top(), min(point.y(), image_rect.bottom()))
        )
        
        return clipped_point

    def line_intersection(self, p1, p2, p3, p4):
        """计算两条线段的交点"""
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        x3, y3 = p3.x(), p3.y()
        x4, y4 = p4.x(), p4.y()
        
        denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
        if abs(denom) < 1e-10:  # 平行线
            return None
            
        t = ((x1-x3)*(y3-y4) - (y1-y3)*(x3-x4)) / denom
        u = -((x1-x2)*(y1-y3) - (y1-y2)*(x1-x3)) / denom
        
        if 0 <= t <= 1 and 0 <= u <= 1:
            return QPointF(x1 + t*(x2-x1), y1 + t*(y2-y1))
        return None

    def clip_polygon_to_edge(self, polygon, edge_start, edge_end):
        """用一条边裁剪多边形（Sutherland-Hodgman算法的一部分）"""
        if len(polygon) < 2:
            return []
            
        output_list = []
        
        for i in range(len(polygon)):
            current_point = polygon[i]
            prev_point = polygon[i-1] if i > 0 else polygon[-1]
            
            # 计算当前点和前一个点相对于裁剪边的位置
            # 使用叉积判断点在边的哪一侧
            edge_vec = edge_end - edge_start
            to_current = current_point - edge_start
            to_prev = prev_point - edge_start
            
            # 叉积：正表示在边的一侧，负表示在另一侧，0表示在边上
            cross_current = edge_vec.x() * to_current.y() - edge_vec.y() * to_current.x()
            cross_prev = edge_vec.x() * to_prev.y() - edge_vec.y() * to_prev.x()
            
            # 假设边的"内部"是叉积为负的一侧（顺时针方向的内部）
            is_current_inside = cross_current <= 0
            is_prev_inside = cross_prev <= 0
            
            if is_current_inside:
                if not is_prev_inside:
                    # 从外到内，需要添加交点
                    intersection = self.line_intersection(prev_point, current_point, edge_start, edge_end)
                    if intersection:
                        output_list.append(intersection)
                # 添加当前点
                output_list.append(current_point)
            elif is_prev_inside:
                # 从内到外，需要添加交点
                intersection = self.line_intersection(prev_point, current_point, edge_start, edge_end)
                if intersection:
                    output_list.append(intersection)
        
        return output_list

    def clip_polygon_to_image(self, polygon_points):
        """使用Sutherland-Hodgman算法将多边形裁剪到图片边界内"""
        if not self.image_widget or len(polygon_points) < 3:
            return None
            
        # 获取图片的边界矩形
        image_rect = self.image_widget.boundingRect()
        
        # 定义矩形的四个顶点（顺时针）
        top_left = image_rect.topLeft()
        top_right = image_rect.topRight()
        bottom_right = image_rect.bottomRight()
        bottom_left = image_rect.bottomLeft()
        
        # 依次用四个边裁剪
        clipped = list(polygon_points)
        
        # 上边（从右到左）
        clipped = self.clip_polygon_to_edge(clipped, top_right, top_left)
        if len(clipped) < 3:
            return None
            
        # 左边（从上到下）
        clipped = self.clip_polygon_to_edge(clipped, top_left, bottom_left)
        if len(clipped) < 3:
            return None
            
        # 下边（从左到右）
        clipped = self.clip_polygon_to_edge(clipped, bottom_left, bottom_right)
        if len(clipped) < 3:
            return None
            
        # 右边（从下到上）
        clipped = self.clip_polygon_to_edge(clipped, bottom_right, top_right)
        
        if len(clipped) >= 3:
            return QPolygonF(clipped)
        return None

    def _get_vertex_at_pos(self, item, view_pos):
        """辅助函数：获取鼠标位置下的顶点/角点索引，如果没点中则返回None"""
        scene_pos = self.mapToScene(view_pos)
        local_pos = item.mapFromScene(scene_pos)
        
        corner_points = []
        if isinstance(item, QGraphicsRectItem):
            rect = item.rect()
            corner_points = [rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()]
        elif isinstance(item, QGraphicsPolygonItem):
            polygon = item.polygon()
            corner_points = [polygon.at(i) for i in range(polygon.count())]

        # 检查点击位置是否足够接近任何一个角点
        for i, point in enumerate(corner_points):
            if QLineF(local_pos, point).length() < 8: # 8像素的容差
                return i
        return None
