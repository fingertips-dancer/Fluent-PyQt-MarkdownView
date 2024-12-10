import os
import typing as t

from PyQt5.QtCore import Qt, QPointF, QRect, QMargins, QRectF, QSizeF, QPoint, QTimer,QEvent
from PyQt5.QtGui import QFontMetrics, QColor, QWheelEvent, QCursor
from PyQt5.QtGui import QPainter, QPaintEvent, QMouseEvent, QKeyEvent, QInputMethodEvent, QKeySequence
from PyQt5.QtWidgets import QAction, QApplication, QScrollArea
from qfluentwidgets import Action,SmoothScrollDelegate
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import RoundMenu
from qfluentwidgets import ThemeColor


class ScrollDelegate(SmoothScrollDelegate):
    def __init__(self,parent):
        super(ScrollDelegate, self).__init__(parent)
        self.vScrollBar.installEventFilter(self)

    def eventFilter(self, obj, e: QEvent):
        if obj is self.vScrollBar:
            # 进入切换 cursor shape
            if e.type() == QEvent.Enter:
                self.parent().setCursor(Qt.ArrowCursor)
        super(ScrollDelegate, self).eventFilter(obj,e)
        return False
