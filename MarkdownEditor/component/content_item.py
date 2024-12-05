from PyQt5.QtCore import QMargins
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QWidget, QScrollArea

from ..cache_paint import CachePaint
from ..cursor import MarkdownCursor
from ..markdown_ast import MarkdownASTBase
from ..style import MarkdownStyle


class AbstractContentItem(QWidget):
    def __init__(self, parent, cachePaint: CachePaint, ast: MarkdownASTBase):
        super(AbstractContentItem, self).__init__(parent=parent)
        self.__ast: MarkdownASTBase = ast
        self._cachePaint: CachePaint = cachePaint
        self._pixmapCache = None

    def __get_the_base_scoll(self) -> QWidget:
        return self.parent().parent().parent()

    def pageMargins(self) -> QMargins:
        margins = self.__get_the_base_scoll()._margins
        return QMargins(margins.left(), 0, margins.right(), 0)

    def cursor(self) -> MarkdownCursor:
        return self.__get_the_base_scoll().cursor()

    def ast(self) -> MarkdownASTBase:
        return self.__ast

    def reset(self):
        self._pixmapCache = None

    def inViewport(self) -> bool:
        w: QScrollArea = self.__get_the_base_scoll()
        view = w.viewport()
        t = w.verticalScrollBar().value()
        b = w.verticalScrollBar().value() + view.height()
        return (t < self.y() < b) or \
               (t < self.y() + self.height() < b) or \
               (self.y() < t < b < self.y() + self.height())

    def viewpot(self) -> QWidget:
        return self.__get_the_base_scoll().viewport()


class ContentItem(AbstractContentItem):

    def render_(self):
        temp = QPixmap(10, 10)
        painter = QPainter(temp)
        # 绘制缓存
        self._cachePaint.reset()
        self._cachePaint.setPainter(painter)
        self._cachePaint.setPaperWidth(self.width())
        self._cachePaint.setMargins(self.pageMargins())
        self._cachePaint.newParagraph()  # 重置段落

        # 渲染登记
        self.ast().render(ht=self._cachePaint, style=MarkdownStyle(), cursor=self.cursor())
        painter.end()
        del temp, painter
        # 局部更新 不刷新缓存
        pixmap = self._cachePaint.render(resetCache=False)[self.ast()]
        self._pixmapCache = pixmap
        # 计算需要的 verticalScroll
        self.setFixedHeight(pixmap.height())
        return pixmap

    def resizeEvent(self, event) -> None:
        if self.inViewport() or self.cursor().ast() not in self._cachePaint.cachePxiamp():
            self.setFixedWidth(self.viewpot().width())
            pixmap = self.render_()
        else:
            self.setFixedHeight(1)
        return
        super(ContentItem, self).resizeEvent(event)
        # 如果不在视图内,懒更新
        # 但如果是cursor在其中则强制更新
        print(self.inViewport() or self.cursor().ast() not in self._cachePaint.cachePxiamp())
        if self.inViewport() or self.cursor().ast() not in self._cachePaint.cachePxiamp():
            # print(123123123123123123123)
            pixmap = self.render_()
        else:
            self.setFixedHeight(1)
            self.reset()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        if not isinstance(self._pixmapCache, QPixmap) or self.viewpot().width() != self.width():
            self.setFixedWidth(self.viewpot().width())
            self.render_()
        try:
            painter.drawPixmap(0, 0, self._pixmapCache)
            painter.end()
        except:
            print(self._pixmapCache)
