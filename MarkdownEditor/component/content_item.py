import typing as t

from PyQt5.QtCore import QMargins, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QPixmap, QResizeEvent, QPaintEvent, QFont
from PyQt5.QtWidgets import QWidget, QScrollArea, QListWidgetItem

from .collapse_button import CollapseButton
from ..cache_paint import CachePaint
from ..cursor import MarkdownCursor
from ..markdown_ast import MarkdownASTBase
from ..style import MarkdownStyle


class ListItem(QListWidgetItem):
    def __init__(self, ast: MarkdownASTBase):
        super(ListItem, self).__init__()
        self.__ast = ast

    def ast(self) -> MarkdownASTBase:
        return self.__ast


class AbstractContentItem(QWidget):
    def __init__(self, parent, cachePaint: CachePaint, ast: MarkdownASTBase):
        self.__view = parent
        self.__upItem: AbstractContentItem = None
        self.__downItem: AbstractContentItem = None
        super(AbstractContentItem, self).__init__(parent=parent)
        self.__ast: MarkdownASTBase = None
        self._cachePaint: CachePaint = cachePaint
        self._pixmapCache = None
        # set
        self.setAST(ast=ast)

    def setUpItem(self, item: t.Optional["AbstractContentItem"]):
        # self.move(0, 2000)
        # return

        """ set up item """
        if self.__upItem:
            self.__upItem.removeEventFilter(self)

        self.__upItem = item
        if isinstance(item, AbstractContentItem):
            item.installEventFilter(self)
            # sync
            if item.downItem() != self:
                item.setDownItem(item=self)

    def setDownItem(self, item: t.Optional["AbstractContentItem"]):
        # self.move(0, 2000)
        # return
        """ set up item """
        if self.__downItem:
            self.__downItem.removeEventFilter(self)

        self.__downItem = item
        if isinstance(item, AbstractContentItem):
            item.installEventFilter(self)
            # sync
            if item.upItem() != self:
                item.setUpItem(item=self)

    def setAST(self, ast: MarkdownASTBase):
        self.__ast = ast

    def enterEvent(self, event) -> None:
        super(AbstractContentItem, self).enterEvent(event)
        self.setMouseTracking(True)  # mouse tracking

    def leaveEvent(self, event) -> None:
        super(AbstractContentItem, self).leaveEvent(event)
        self.setMouseTracking(False)  # mouse tracking

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
        w: QScrollArea = self.view()
        view = w.viewport()
        t = w.verticalScrollBar().value()
        b = w.verticalScrollBar().value() + view.height()
        return (self.geometry().bottom() >= t) and self.y() <= b

    def viewpot(self) -> QWidget:
        return self.view().viewport()

    def view(self) -> QWidget:
        return self.__view

    def upItem(self) -> 'AbstractContentItem':
        return self.__upItem

    def downItem(self) -> 'AbstractContentItem':
        return self.__downItem

    def markdownStyle(self) -> MarkdownStyle:
        return self.view().markdownStyle()

    def render_(self):
        raise NotImplementedError


class ContentItem(AbstractContentItem):
    collapseRequested = pyqtSignal(AbstractContentItem)

    def __init__(self, parent, cachePaint: CachePaint, ast: MarkdownASTBase):
        self.__renderWidth = 0
        self.__callopseButton: CollapseButton = None
        self.__isCollapsing = False
        super(ContentItem, self).__init__(parent=parent, cachePaint=cachePaint, ast=ast)
        self.__listItem = ListItem(ast=ast)

    def setAST(self, ast: MarkdownASTBase):
        super(ContentItem, self).setAST(ast=ast)
        if ast.isShowCollapseButton() and self.__callopseButton is None:
            self.__callopseButton = CollapseButton.new(self)
            self.__callopseButton.clicked.connect(lambda: self.collapseRequested.emit(self))
        elif not ast.isShowCollapseButton() and self.__callopseButton is not None:
            self.__callopseButton.deleteLater()
            self.__callopseButton = None

    def setIsCollapsing(self, _is: bool) -> bool:
        self.__isCollapsing = _is

    def render_(self):
        temp = QPixmap(10, 10)
        painter = QPainter(temp)
        painter.setFont(self.markdownStyle().hintFont(font=QFont(), ast='root'))
        self.__renderWidth = self.width()
        # 绘制缓存
        self._cachePaint.reset()
        self._cachePaint.setPainter(painter)
        self._cachePaint.setPaperWidth(self.width())
        self._cachePaint.setMargins(self.pageMargins())
        self._cachePaint.newParagraph()  # 重置段落

        # 渲染登记
        self.ast().render(ht=self._cachePaint, style=self.markdownStyle(), cursor=self.cursor())
        painter.end()
        del temp, painter
        # 局部更新 不刷新缓存
        pixmap = self._cachePaint.render(resetCache=False)[self.ast()]
        self._pixmapCache = pixmap
        # 计算需要的 verticalScroll
        self.setFixedHeight(pixmap.height())
        self.__listItem.setSizeHint(pixmap.size())

        # callopse button
        if self.__callopseButton:
            lh = self._cachePaint.lineHeight(ast=self.ast(), pos=0)
            self.__callopseButton.setFixedSize(int(lh * 0.618), int(lh * 0.618))
            self.__callopseButton.move(self.pageMargins().left() - self.__callopseButton.width(),
                                       (lh - self.__callopseButton.height()) // 2)

        return pixmap

    def resizeEvent(self, event: QResizeEvent) -> None:
        if self.inViewport() or self.cursor().ast() not in self._cachePaint.cachePxiamp():
            self.setFixedWidth(self.viewpot().width())
            super(ContentItem, self).resizeEvent(event)
        else:
            pass

    def paintEvent(self, event: QPaintEvent) -> None:
        if self.isCollapsing():
            return
        super(ContentItem, self).paintEvent(event)
        if not isinstance(self._pixmapCache, QPixmap) or self.viewpot().width() != self.width():
            self.setFixedWidth(self.viewpot().width())
            self.render_()


        try:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self._pixmapCache)
            painter.end()
        except:
            print(self._pixmapCache)

    def show(self) -> None:
        super(ContentItem, self).show()
        if self._pixmapCache is None:
            self.render_()
        else:
            self.setFixedHeight(self._pixmapCache.height())

    def hide(self) -> None:
        super(ContentItem, self).hide()
        self.setFixedHeight(0)

    def height(self) -> int:
        return 0 if self.isHidden() else super(ContentItem, self).height()

    def isCollapseSubItem(self) -> bool:
        """ 是否折叠 """
        return self.__callopseButton.isCollapse()

    def isCollapsing(self) -> bool:
        return self.__isCollapsing

    def cursorBases(self, returnAst=False) -> t.List[QPoint] or t.List[t.Tuple[MarkdownASTBase, QPoint]]:
        return self._cachePaint.cursorPluginBases(self.ast(), returnAst=returnAst)

    def lineHeight(self, pos: int):
        if self._pixmapCache is None:
            self.render_()
        return self._cachePaint.lineHeight(ast=self.ast(), pos=pos)

    def indentation(self, pos: int):
        return self._cachePaint.indentation(ast=self.ast(), pos=pos)

    def renderWidth(self) -> int:
        """ 绘制是使用的 width"""
        return self.__renderWidth

    def setFixedHeight(self, h: int) -> None:
        super(ContentItem, self).setFixedHeight(0 if self.isCollapsing() else h)
