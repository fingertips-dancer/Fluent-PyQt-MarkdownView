from PyQt5.QtCore import QMargins, pyqtSignal
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QWidget, QScrollArea

from .collapse_button import CollapseButton
from ..cache_paint import CachePaint
from ..cursor import MarkdownCursor
from ..markdown_ast import MarkdownASTBase
from ..style import MarkdownStyle


class AbstractContentItem(QWidget):
    def __init__(self, parent, cachePaint: CachePaint, ast: MarkdownASTBase):
        self.__view = parent
        super(AbstractContentItem, self).__init__(parent=parent)
        self.__ast: MarkdownASTBase = None
        self._cachePaint: CachePaint = cachePaint
        self._pixmapCache = None
        # set
        self.setAST(ast=ast)

    def setAST(self, ast: MarkdownASTBase):
        self.__ast = ast

    def __get_the_base_scoll(self) -> QWidget:
        return self.parent().parent().parent()

    def pageMargins(self) -> QMargins:
        margins = self.view()._margins
        return QMargins(margins.left(), 0, margins.right(), 0)

    def cursor(self) -> MarkdownCursor:
        return self.view().cursor()

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

    def view(self) -> QWidget:
        return self.__view


class ContentItem(AbstractContentItem):
    collapseRequested = pyqtSignal(AbstractContentItem)

    def __init__(self, parent, cachePaint: CachePaint, ast: MarkdownASTBase):
        self.__callopseButton: CollapseButton = None
        super(ContentItem, self).__init__(parent=parent, cachePaint=cachePaint, ast=ast)

    def setAST(self, ast: MarkdownASTBase):
        super(ContentItem, self).setAST(ast=ast)
        if ast.isShowCollapseButton() and self.__callopseButton is None:
            self.__callopseButton = CollapseButton.new(self)
            self.__callopseButton.clicked.connect(lambda :self.collapseRequested.emit(self))
        elif not ast.isShowCollapseButton() and self.__callopseButton is not None:
            self.__callopseButton.deleteLater()
            self.__callopseButton = None

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

        # callopse button
        if self.__callopseButton:
            lh = self._cachePaint.lineHeight(ast=self.ast(), pos=0)
            self.__callopseButton.setFixedSize(int(lh * 0.618), int(lh * 0.618))
            self.__callopseButton.move(self.pageMargins().left() - self.__callopseButton.width(),
                                       (lh - self.__callopseButton.height()) // 2)

        return pixmap

    def resizeEvent(self, event) -> None:
        if self.inViewport() or self.cursor().ast() not in self._cachePaint.cachePxiamp():
            self.setFixedWidth(self.viewpot().width())
            pixmap = self.render_()
            super(ContentItem, self).resizeEvent(event)
        else:
            self.setFixedHeight(1)
        return

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

    def isCollapse(self) -> bool:
        """ 是否折叠 """
        return self.__callopseButton.isCollapse()

