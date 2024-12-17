import typing as t

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QFontMetrics, QPixmap, QColor

from ..abstruct import AbstructTextParagraph
# from .cursor import MarkdownCursor
from ..markdown_ast import MarkdownASTBase, MarkdownAstRoot


class TextParagraph(AbstructTextParagraph):
    __renderCache: QPixmap

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
        # 没有缓存
        if len(self._cache) == 0: return QPixmap(0, 0)
        # 没有新的内容直接输出缓存
        if not self.needRerender():
            return self.__renderCache

        # 0. 预处理
        self.initPaintPoint(0)
        # 创建一个透明的 QPixmap，尺寸为 400x300
        pixmap = QPixmap(self.viewWdith(), 1000)
        pixmap.fill(QColor(0, 0, 0, 0))  # 使用完全透明的颜色
        painter = QPainter(pixmap)

        # 确定 ast (root 的 子项)
        self.setAST(self._cache[0][2])
        while not isinstance(self.ast().parent, MarkdownAstRoot):
            self.setAST(self.ast().parent)
        # 清空 cursor bases
        self.clearAllcursorBases()
        # 计算一行的高度
        self.setLineHeight(max(QFontMetrics(font).height() for method, data, ast, font, brush, pen in self._cache))

        # 1.render
        # 1. memorize the cursor of different ast, to cal rect of ast
        if self.backgroundEnable():
            self.initPaintPoint(self.backgroundMargins().top())
        if len(self.cursorBases()) != 0: raise Exception()
        for method, data, ast, font, brush, pen in self._cache:
            self.registerNowPaintingAst(ast=ast)
            # render
            painter.setPen(pen)
            painter.setFont(font)
            painter.setBrush(brush)
            method(self, data=data, ast=ast, painter=painter)

        # 3. 对齐
        # 3.1 默认左对齐
        if self.align() != self.AlignLeft:
            bs = self.cursorBases()
            ys = {b.y() for _, b in bs}
            pageMargins = self.pageMargins()
            eraseWidth = self.viewWdith() - pageMargins.left() - pageMargins.right()
            for y in ys:
                it = [b for _, b in bs if b.y() == y]
                _max_p = max(it, key=lambda x: x.x(), default=None)
                _min_p = min(it, key=lambda x: x.x(), default=None)
                if _min_p is None or _max_p is None: continue
                # 偏移量
                offset = QPointF(self.viewWdith() - self.margins().right() - _max_p.x(), 0)
                if self.align() == self.AlignCenter: offset = offset / 2
                # 先擦除再转移
                # continue
                rect = QRectF(QPointF(pageMargins.left(), y), QPointF(_max_p.x(), y + self.lineHeight()))
                transfome = pixmap.copy(rect.toRect())

                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.eraseRect(QRectF(pageMargins.left(), rect.top(), eraseWidth, self.lineHeight()))
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.drawPixmap(QPointF(0, y) + offset, transfome)

        # 4. 绘制背景
        # 4.1 先把之前的内容截取
        # 4.2 绘制背景后再重绘回去
        if self.backgroundEnable():
            # _pixmap = pixmap.copy(QRectF(0, 0, self.viewWdith(), self.paintPoint().y()).toRect())
            # pixmap.fill(QColor(0, 0, 0, 0))
            painter.setCompositionMode(QPainter.CompositionMode_DestinationOver)
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.backgroundColor())
            rect = QRectF(self.pageMargins().left() + self.indentation(), 0,
                          self.viewWdith() - self.pageMargins().left() - self.indentation() - self.pageMargins().right(),
                          self.paintPoint().y() + self.backgroundMargins().bottom())
            painter.drawRoundedRect(rect, self.backgroundRaidus(), self.backgroundRaidus())
            # painter.drawPixmap(0, 0, _pixmap)
            self.setPaintPoint(rect.bottomLeft())

        # 4. 结束绘制
        # 4.1 截取出有效内容
        # 4.2 保存为缓存,然后重置 NeedRerender
        painter.end()
        self.setNeedRerender(False)
        rect = QRectF(0, 0, self.viewWdith(), self.paintPoint().y()).toRect()
        if rect.height() != 0:
            self.__renderCache = pixmap.copy(QRectF(0, 0, self.viewWdith(), self.paintPoint().y()).toRect())
        else:
            self.__renderCache = QPixmap(pixmap.width(), 0)
        return self.__renderCache

    """ cache """

    def pullRenderCache(self, func: int or str, data, painter: QPainter, ast: MarkdownASTBase):
        self.setNeedRerender(True)
        self._cache.append((self.renderFunctions[func], data, ast, painter.font(), painter.brush(), painter.pen()))
