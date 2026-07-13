from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QRectF
import math

"""Генерация векторных иконок интерфейса без внешних файлов."""


def create_icon(icon_type: str, size: int = 24, color: str = '#1890ff') -> QIcon:
    # Рисуем иконки кодом, чтобы масштабирование оставалось четким на любом DPI.
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    pen = QPen(QColor(color))
    pen.setWidth(2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    
    margin = size * 0.15
    w = size - 2 * margin
    h = size - 2 * margin
    
    if icon_type == 'apply':
        painter.setBrush(QColor(color))
        points = [
            (margin + w * 0.8, margin + h * 0.2),
            (margin + w * 0.4, margin + h * 0.7),
            (margin + w * 0.2, margin + h * 0.5),
        ]
        pen.setWidth(3)
        painter.setPen(pen)
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]),
                           int(points[i+1][0]), int(points[i+1][1]))
    
    elif icon_type == 'play':
        painter.setBrush(QColor(color))
        pen.setWidth(0)
        painter.setPen(pen)
        points = [
            (margin + w * 0.25, margin),
            (margin + w * 0.25, margin + h),
            (margin + w * 0.85, margin + h * 0.5),
        ]
        from PyQt6.QtGui import QPolygonF
        from PyQt6.QtCore import QPointF
        poly = QPolygonF([QPointF(p[0], p[1]) for p in points])
        painter.drawPolygon(poly)
    
    elif icon_type == 'stop':
        painter.setBrush(QColor(color))
        pen.setWidth(0)
        painter.setPen(pen)
        rect = QRectF(margin + w * 0.2, margin + h * 0.2,
                     w * 0.6, h * 0.6)
        painter.drawRect(rect)
    
    elif icon_type == 'open':
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        folder_h = h * 0.6
        folder_y = margin + h - folder_h
        painter.drawRect(QRectF(margin, folder_y, w, folder_h))
        tab_w = w * 0.4
        tab_h = h * 0.25
        painter.drawRect(QRectF(margin, folder_y - tab_h, tab_w, tab_h))
    
    elif icon_type == 'save':
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRectF(margin, margin, w, h))
        tab_size = h * 0.3
        painter.drawLine(int(margin + w - tab_size), int(margin),
                        int(margin + w), int(margin + tab_size))
        painter.drawLine(int(margin + w * 0.3), int(margin + h * 0.5),
                        int(margin + w * 0.7), int(margin + h * 0.5))
        painter.drawLine(int(margin + w * 0.5), int(margin + h * 0.5),
                        int(margin + w * 0.5), int(margin + h * 0.85))
    
    elif icon_type == 'generator':
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        points_count = 50
        for i in range(points_count - 1):
            x1 = margin + (w * i / points_count)
            x2 = margin + (w * (i + 1) / points_count)
            y1 = margin + h / 2 + h * 0.3 * math.sin(i * math.pi / 8)
            y2 = margin + h / 2 + h * 0.3 * math.sin((i + 1) * math.pi / 8)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    elif icon_type == 'analyzer':
        pen.setWidth(2)
        painter.setPen(pen)
        heights = [0.3, 0.6, 0.9, 0.7, 0.4, 0.5, 0.8]
        bar_w = w / len(heights)
        for i, h_frac in enumerate(heights):
            x = margin + i * bar_w
            bar_h = h * h_frac
            painter.drawLine(int(x + bar_w * 0.5), int(margin + h),
                           int(x + bar_w * 0.5), int(margin + h - bar_h))
    
    elif icon_type == 'microphone':
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        mic_w = w * 0.4
        mic_h = h * 0.5
        mic_x = margin + w * 0.3
        mic_y = margin + h * 0.1
        painter.drawRoundedRect(QRectF(mic_x, mic_y, mic_w, mic_h), 5, 5)
        arc_y = mic_y + mic_h
        arc_h = h * 0.25
        painter.drawArc(QRectF(mic_x - mic_w * 0.2, arc_y, mic_w * 1.4, arc_h * 2),
                       0, 180 * 16)
        painter.drawLine(int(margin + w * 0.5), int(arc_y + arc_h),
                        int(margin + w * 0.5), int(margin + h * 0.95))
    
    elif icon_type == 'tutorial':
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRectF(margin, margin, w, h))
        for i in range(3):
            y = margin + h * (0.25 + i * 0.25)
            painter.drawLine(int(margin + w * 0.2), int(y),
                           int(margin + w * 0.8), int(y))
    
    elif icon_type == 'about':
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(margin, margin, w, h))
        painter.drawText(QRectF(margin, margin + h * 0.15, w, h * 0.4),
                        Qt.AlignmentFlag.AlignCenter, 'i')
    
    elif icon_type == 'start':
        painter.setBrush(QColor('#00ff41'))
        pen.setWidth(0)
        painter.setPen(pen)
        painter.drawEllipse(QRectF(margin + w * 0.2, margin + h * 0.2,
                                  w * 0.6, h * 0.6))
    
    elif icon_type == 'pause':
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(int(margin + w * 0.35), int(margin + h * 0.2),
                        int(margin + w * 0.35), int(margin + h * 0.8))
        painter.drawLine(int(margin + w * 0.65), int(margin + h * 0.2),
                        int(margin + w * 0.65), int(margin + h * 0.8))
    
    painter.end()
    return QIcon(pixmap)
