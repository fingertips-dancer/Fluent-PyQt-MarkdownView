
import os
import time
import typing as t

from PyQt5.QtCore import Qt, QPointF, QRect, QMargins, QRectF, QSizeF, QTimer, QPoint
from PyQt5.QtGui import QFontMetrics, QColor,QPixmap
from PyQt5.QtGui import QPainter, QPaintEvent, QMouseEvent, QKeyEvent, QInputMethodEvent, QKeySequence
from PyQt5.QtWidgets import QAction, QApplication, QWidget, QScrollArea
from qfluentwidgets import Action
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SmoothScrollDelegate, RoundMenu
from qfluentwidgets import ThemeColor



class Container(QWidget):
    pass