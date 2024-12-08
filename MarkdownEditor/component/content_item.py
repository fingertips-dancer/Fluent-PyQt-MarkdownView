import typing as t

from PyQt5.QtCore import QMargins, pyqtSignal, QEvent, QPoint
from PyQt5.QtGui import QPainter, QPixmap, QResizeEvent, QPaintEvent, QFont,QMouseEvent
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
            self.move(0, self.upItem().y() + self.upItem().height())

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

        if self.upItem():
            self.move(0, self.upItem().y() + self.upItem().height())

    def setAST(self, ast: MarkdownASTBase):
        self.__ast = ast

    def eventFilter(self, obj, event) -> bool:
        if event.type() == 16:
            return False
        elif event.type() == QEvent.DeferredDelete:  # 销毁
            if self.upItem() is obj:
                self.setUpItem(None)
            elif self.downItem() is obj:
                self.setDownItem(None)
            return False
        if self.inViewport() and self.__upItem:
            y = self.__upItem.y() + self.__upItem.height()
            self.move(0, y)
        elif obj is self.__upItem and event.type() in (QEvent.Resize, QEvent.Move, QEvent.Hide, QEvent.Show):
            if self.__upItem.inViewport() or self.inViewport():  # <--视图中才更新,防止递归深度太大
                y = self.__upItem.y() + self.__upItem.height()
                self.move(0, y)
        return False

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
        return (t < self.y() < b) or \
               (t < self.y() + self.height() < b) or \
               (self.y() < t < b < self.y() + self.height())

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


class ContentItem(AbstractContentItem):
    collapseRequested = pyqtSignal(AbstractContentItem)

    def __init__(self, parent, cachePaint: CachePaint, ast: MarkdownASTBase):
        self.__callopseButton: CollapseButton = None
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

    def render_(self):
        temp = QPixmap(10, 10)
        painter = QPainter(temp)
        painter.setFont(self.markdownStyle().hintFont(font=QFont(), ast='root'))
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
        return

    def paintEvent(self, event: QPaintEvent) -> None:
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

    def isCollapse(self) -> bool:
        """ 是否折叠 """
        return self.__callopseButton.isCollapse()

    def listItem(self) -> ListItem:
        return self.__listItem

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

    def cursorBases(self,returnAst=False) -> t.List[QPoint] or t.List[t.Tuple[MarkdownASTBase,QPoint]]:
        return self._cachePaint.cursorPluginBases(self.ast(),returnAst=returnAst)

    def lineHeight(self, pos: int):
        return self._cachePaint.lineHeight(ast=self.ast(), pos=pos)

    def indentation(self, pos: int):
        return self._cachePaint.indentation(ast=self.ast(), pos=pos)
