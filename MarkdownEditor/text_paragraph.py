import typing as t

from PyQt5.QtCore import QPointF
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QFontMetrics

from .abstruct import AbstructTextParagraph
# from .cursor import MarkdownCursor
from .markdown_ast import MarkdownASTBase, MarkdownAstRoot


class TextParagraph(AbstructTextParagraph):
    renderFunctions = {}  # 渲染方法

    @classmethod
    def registerRenderFunction(cls, name):
        """ 添加 render function """

        def wapper(func: t.Callable):
            cls.renderFunctions[name] = func
            return func

        return wapper

    def render(self, painter: QPainter) -> int:
        """ 新的 y 位置"""
        if len(self._cache) == 0:
            return self.paintPoint().y()

        # 确定 ast (root 的 子项)
        self.setAST(self._cache[0][2])
        while not isinstance(self.ast().parent, MarkdownAstRoot):
            self.setAST(self.ast().parent)

        # 计算一行的高度
        self.setLineHeight(max(QFontMetrics(font).height() for method, data, ast, font, brush, pen in self._cache))

        sPos = self.paintPoint() + QPointF(0, 0)
        # 1.render
        for method, data, ast, font, brush, pen in self._cache:
            painter.setPen(pen)
            painter.setFont(font)
            painter.setBrush(brush)
            method(self, data=data, ast=ast, painter=painter)

        # 绘制背景
        if self.backgroundColor().alpha() != 0:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.backgroundColor())
            rect = QRectF(self.margins().left() + self.indentation(),
                          sPos.y(),
                          self.viewWdith() - self.margins().left() - self.margins().right() - self.indentation(),
                          self.paintPoint().y() - sPos.y())
            painter.drawRoundedRect(rect, self.backgroundRaidus(), self.backgroundRaidus())

            # repaint
            self.setPaintPoint(sPos)
            self._cursor_bases = []
            for method, data, ast, font, brush, pen in self._cache:
                painter.setPen(pen)
                painter.setFont(font)
                painter.setBrush(brush)
                method(self, data=data, ast=ast, painter=painter)

        return self.paintPoint().y()

    """ cache """

    def pullRenderCache(self, func: int or str, data, painter: QPainter, ast: MarkdownASTBase):
        self._cache.append((self.renderFunctions[func], data, ast, painter.font(), painter.brush(), painter.pen()))
