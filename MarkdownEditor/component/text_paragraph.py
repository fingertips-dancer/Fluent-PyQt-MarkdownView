import typing as t

from PyQt5.QtCore import QPointF
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QFontMetrics, QPixmap, QColor

from ..abstruct import AbstructTextParagraph
# from .cursor import MarkdownCursor
from ..markdown_ast import MarkdownASTBase, MarkdownAstRoot


class TextParagraph(AbstructTextParagraph):
    renderFunctions = {}  # 渲染方法

    @classmethod
    def registerRenderFunction(cls, name):
        """ 添加 render function """

        def wapper(func: t.Callable):
            cls.renderFunctions[name] = func
            return func

        return wapper

    def render(self) -> QPixmap:
        """ 新的 y 位置"""
        if len(self._cache) == 0:
            return QPixmap(0, 0)
        self.setStartY(0)

        # 创建一个透明的 QPixmap，尺寸为 400x300
        pixmap = QPixmap(self.viewWdith(), 1000)
        pixmap.fill(QColor(0, 0, 0, 0))  # 使用完全透明的颜色
        painter = QPainter(pixmap)

        # 确定 ast (root 的 子项)
        self.setAST(self._cache[0][2])
        while not isinstance(self.ast().parent, MarkdownAstRoot):
            self.setAST(self.ast().parent)

        # 计算一行的高度
        self.setLineHeight(max(QFontMetrics(font).height() for method, data, ast, font, brush, pen in self._cache))

        sPos = self.paintPoint() + QPointF(0, 0)

        # 1.render
        if self.backgroundEnable():
            self.setStartY(self.backgroundMargins().top())

        for method, data, ast, font, brush, pen in self._cache:
            painter.setPen(pen)
            painter.setFont(font)
            painter.setBrush(brush)
            method(self, data=data, ast=ast, painter=painter)

        # 绘制背景
        if self.backgroundEnable():
            _pixmap = pixmap.copy(QRectF(0, 0, self.viewWdith(), self.paintPoint().y()).toRect())
            pixmap.fill(QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.backgroundColor())
            rect = QRectF(self.pageMargins().left() + self.indentation(),
                          sPos.y(),
                          self.viewWdith() - self.pageMargins().left() - self.indentation() - self.pageMargins().right(),
                          self.paintPoint().y() - sPos.y() + self.backgroundMargins().bottom())
            painter.drawRoundedRect(rect, self.backgroundRaidus(), self.backgroundRaidus())
            painter.drawPixmap(0, 0, _pixmap)
            self.setPaintPoint(rect.bottomLeft())

        painter.end()
        pixmap = pixmap.copy(QRectF(0, 0, self.viewWdith(), self.paintPoint().y()).toRect())
        return pixmap

    """ cache """

    def pullRenderCache(self, func: int or str, data, painter: QPainter, ast: MarkdownASTBase):
        self._cache.append((self.renderFunctions[func], data, ast, painter.font(), painter.brush(), painter.pen()))
