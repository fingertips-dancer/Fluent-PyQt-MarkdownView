from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPainter
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import TransparentToolButton, isDarkTheme


class CollapseButton(TransparentToolButton):
    """ Collapse button """
    _isCollapse = False

    @classmethod
    def new(self, parent):
        btn = CollapseButton(parent)
        btn.setIsCollapse(is_=False)
        btn.clicked.connect(lambda: btn.setIsCollapse(is_=not btn.isCollapse()))
        return btn

    def setIsCollapse(self, is_: bool) -> None:
        self._isCollapse = is_
        self.setIcon(FIF.CARE_RIGHT_SOLID if is_ else FIF.CARE_DOWN_SOLID)

    def isCollapse(self) -> bool:
        return self._isCollapse

    def _drawIcon(self, icon, painter: QPainter, rect: QRectF):
        pass

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if not self.isPressed:
            w, h = int(self.width() * 0.618 / 1.5), int(self.height() * 0.618 / 1.5)
        else:
            w, h = int(self.width() * 0.382 / 1.5), int(self.height() * 0.382 / 1.5)

        x = (self.width() - w) / 2
        y = (self.height() - h) / 2

        if not isDarkTheme():
            self._icon.render(painter, QRectF(x, y, w, h), fill="#5e5e5e")
        else:
            self._icon.render(painter, QRectF(x, y, w, h), fill="#9c9c9c")

