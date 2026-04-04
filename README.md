<h1 align="center">图片查看工具</h1>

## 打包可执行文件
```bash
pyinstaller -Fw -i assets/image/logo.png --path . app.py -n ImageView
```

## 快捷键
 - `Left` 查看上一张图片
 - `Right` 查看下一张图片
 - `Delete` 删除图片
 - `R` 旋转图片
 - `鼠标双击` 图片自适应窗口

## 示例图

| 暗黑主题 | 浅色主题 |
| :-----: | :-----: |
| ![./assets/demo/dark.png](./assets/demo/dark.png) | ![./assets/demo/light.png](./assets/demo/light.png) |