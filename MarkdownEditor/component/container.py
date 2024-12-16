import time
import typing as t

from PyQt5.QtCore import QRect, QTimer, pyqtSignal, QPoint, QPointF
from PyQt5.QtWidgets import QWidget, QScrollArea

from .content_item import ContentItem
from ..abstruct import AbstractMarkdownEdit
from ..cache_paint import CachePaint
from ..document import MarkDownDocument
from ..markdown_ast import MarkdownASTBase


class Container(QWidget):
    itemCreated = pyqtSignal(ContentItem)
    itemCreatingStarted = pyqtSignal()
    itemCreatingFinished = pyqtSignal()
    Up = 123
    Down = 456
    Self = 789

    def getContentItem(self, ast: MarkdownASTBase, position: int = Self) -> t.Optional[ContentItem]:
        """ get a conntent, if pool is empty, it will create a new content item"""
        # 确定位置
        if position == self.Self:
            ast = ast
        elif position == self.Down:
            ast = ast.downAst()
        elif position == self.Up:
            ast = ast.upAst()
        else:
            raise Exception()
        # 没有ast
        if ast is None: return None

        contentItem = self.__contentItems.get(ast, None)  # 先去 显示池中寻找
        if contentItem:
            return contentItem
        if len(self.__contentItemPoll):
            contentItem = self.__contentItemPoll.pop()
        else:
            contentItem = ContentItem(parent=self.area(), ast=ast)
        self.__contentItems[ast] = contentItem
        contentItem.setParent(self)
        contentItem.setAST(ast)
        upAst = ast.upAst()
        downAst = ast.downAst()
        if upAst in self.__contentItems: contentItem.setUpItem(self.__contentItems[upAst])
        if downAst in self.__contentItems: contentItem.setDownItem(self.__contentItems[downAst])
        contentItem.hide()
        return contentItem

    def removeContentItem(self, ast):
        contentItem = self.__contentItems.pop(ast)
        contentItem.reset()
        contentItem.hide()
        self.__contentItemPoll.add(contentItem)
        if ast in self.__nowShowAst:
            self.__nowShowAst.remove(ast)

    def createContentItem(self, ast) -> ContentItem:
        _item = ContentItem(parent=self.area(), ast=ast)
        # _item.collapseRequested.connect(self.onCollapseRequestedEvent)
        _item.setParent(self)
        self.__contentItems[ast] = _item
        self.itemCreated.emit(_item)
        return _item

    def autoUpdateMarkdownItem(self, maxUpdateNum=10, updatesEnabled=True):
        """
        渲染到缓存
        :param asts: 确定重绘的范围,None表示全部
        :return:
        """
        # st = time.time()
        self.setUpdatesEnabled(False)  # <--禁止重绘,防止闪烁
        self.area().setUpdatesEnabled(False)
        # 使用缓存来绘制
        self.__updateItemer.stop()

        # 删除多余的item
        have_init_items = set(self.__contentItems.keys())
        need_init_items = set(self.document().ast().children)
        need_del_items = have_init_items.difference(need_init_items)
        if len(need_del_items):
            for i, ast in enumerate(need_del_items):
                self.removeContentItem(ast)

        # 差集,查看需要初始化的item
        # 需要保持顺序
        not_init_items = [ast for ast in self.document().ast().children if ast not in have_init_items]
        # 初始化
        _len = len(not_init_items)
        if _len != 0 and not self.__creating:
            self.__creating = True
            self.itemCreatingStarted.emit()
        elif _len == 0 and self.__creating:
            self.__creating = False
            self.itemCreatingFinished.emit()

        for i, ast in enumerate(not_init_items[:0]):
            item = self.createContentItem(ast=ast)
            self.__contentItems[ast] = item
            upAst = ast.upAst()
            downAst = ast.downAst()
            if upAst in self.__contentItems: item.setUpItem(self.__contentItems[upAst])
            if downAst in self.__contentItems: item.setDownItem(self.__contentItems[downAst])
            item.hide()

        self.updateShowLayout()
        # st = time.time()
        self.__updateItemer.start(10)
        self.setUpdatesEnabled(True)  # <--重绘,防止闪烁
        self.area().setUpdatesEnabled(True)  # <--重绘,防止闪烁

    def preprocess(self, item: ContentItem, y):
        item.show()
        if item.renderWidth() != self.width():
            item.setFixedWidth(self.width())
            item.reset()
            item.render_()
        if item.y() != y:
            item.move(0, y)

    def updateShowLayout(self):
        """ 更新显示布局 """
        if not self.isVisible() or self.isHidden(): return
        area: QScrollArea = self.area()
        # 1. when it have not item be show
        self.setUpdatesEnabled(False)  # <--禁止重绘,防止闪烁

        # 2. determine which content item need to show
        if len(self.__nowShowAst) == 0:
            item = self.getContentItem(self.document().ast().children[0])
            self.preprocess(item, y=0)
            self.__nowShowAst.append(item.ast())
            h = self.height() - item.height()
            while h >= 0 and self.getContentItem(item.ast(), position=self.Down):
                downItem = self.getContentItem(item.ast(), position=self.Down)
                self.preprocess(downItem, y=item.geometry().bottom())
                self.__nowShowAst.append(downItem.ast())
                item = downItem
                h = h - item.height()

        else:
            c_item = self.getContentItem(ast=self.__nowShowAst[0])
            self.preprocess(c_item, y=c_item.geometry().y())
            nowShowAst = [c_item.ast()]

            # up
            item = c_item
            thresh_y = c_item.geometry().y() - area.verticalScrollBar().value()
            while thresh_y >= -300 and self.getContentItem(item.ast(), position=self.Up):
                upItem = self.getContentItem(item.ast(), position=self.Up)
                self.preprocess(upItem, y=item.geometry().y())
                upItem.move(0, max(0, item.y() - upItem.height()))
                nowShowAst.insert(0, upItem.ast())
                item = upItem
                thresh_y = thresh_y - item.height()
            st = time.time()

            # down
            item = c_item
            thresh_y = area.verticalScrollBar().value() + area.height() - c_item.geometry().bottom()
            while thresh_y >= -300 and self.getContentItem(item.ast(), position=self.Down):
                downItem = self.getContentItem(item.ast(), position=self.Down)
                self.preprocess(downItem, y=item.geometry().bottom())
                nowShowAst.append(downItem.ast())
                item = downItem
                thresh_y = thresh_y - item.height()
            # hide
            need_hide_ast = set(self.__nowShowAst).difference(set(nowShowAst))
            for ast in need_hide_ast:
                self.removeContentItem(ast)
                # self.__contentItems[ast].hide()

            # 重排保证一致
            # 是排序第一个的ast
            if self.document().ast().children[0] in nowShowAst:
                if self.__contentItems[nowShowAst[0]].y() != 0:
                    # 如果移动,可能导致viewport中没有item
                    # 需要调节 verticalScrollBar
                    offset = self.__contentItems[nowShowAst[0]].y()
                    area.verticalScrollBar().setValue(area.verticalScrollBar().value()-offset)
                    self.__contentItems[nowShowAst[0]].move(0, 0)
                    for ast in nowShowAst[1:]:
                        item = self.__contentItems[ast]
                        item.move(0, item.upItem().geometry().bottom())

            # hide over up item
            for ast in nowShowAst.copy():
                if self.__contentItems[ast].geometry().bottom() < area.verticalScrollBar().value() - 300:
                    self.removeContentItem(ast)
                    # self.__contentItems[ast].hide()
                    nowShowAst.pop(0)
                    # break
                else:
                    break
            self.__nowShowAst = nowShowAst
            # print("update11", time.time() - st)

        last_show_item = self.__contentItems[self.__nowShowAst[-1]]
        b = last_show_item.geometry().bottom()
        guess = max(self.__bottom, b + 20)  # <--不是最后一个
        self.__bottom = b if last_show_item.ast() is self.document().ast().children[-1] else guess
        self.setFixedHeight(max(self.__bottom, 0))
        self.setUpdatesEnabled(True)  # <--禁止重绘,防止闪烁
        # print("当前绘制, 显示数量:", len(self.__nowShowAst), last_show_item.geometry())
        # print("当前绘制, 绘制数量:", len(self.__contentItems), last_show_item.ast() is self.document().ast().children[-1])
        # print("当前绘制, 缓存数量:", len(self.__contentItemPoll), self.__bottom)
        # print("当前绘制, height:", self.height(), self.area().height(), area.verticalScrollBar().value())

    def __init__(self, parent: AbstractMarkdownEdit):
        self.__area: AbstractMarkdownEdit or QScrollArea = parent
        self.__contentItems: t.Dict[MarkdownASTBase, ContentItem] = {}
        self.__yCache: t.Dict[MarkdownASTBase, QRect] = {}
        self.__nowShowAst: t.List[MarkdownASTBase] = []
        self.__creating = False
        self.__bottom = 0  # 底部坐标
        self.__contentItemPoll: t.Set[ContentItem] = set()

        super(Container, self).__init__(parent)
        self.setStyleSheet("background-color:transparent;")
        self.setMouseTracking(True)  # 鼠标追踪

        # auto update
        self.__updateItemer = QTimer()
        self.__updateItemer.setSingleShot(True)
        self.__updateItemer.timeout.connect(self.autoUpdateMarkdownItem)

    def area(self) -> t.Union[AbstractMarkdownEdit or QScrollArea]:
        return self.__area

    def contentItemCache(self, ast: MarkdownASTBase = None) -> t.Dict[MarkdownASTBase, ContentItem] or ContentItem:
        if ast:
            return self.__contentItems.get(ast, None)
        return self.__contentItems

    def document(self) -> MarkDownDocument:
        return self.area().document()

    def astIn(self, pos: QPoint) -> MarkdownASTBase:
        item = self.childAt(pos)
        if not isinstance(item, ContentItem):
            return None
        return item.ast()

    def cursorBaseIn(self, pos: t.Union[QPointF, QPoint]) -> t.Optional[t.Tuple[MarkdownASTBase, int]]:
        """ overload """
        if isinstance(pos, QPointF): pos = pos.toPoint()
        item: ContentItem = self.childAt(pos)
        if not isinstance(item, ContentItem): return None, None
        # filter the cursor of 'y < pos'
        in_pos = pos - item.pos()
        cursorBases = [(i, p) for i, p in enumerate(item.cursorBases()) if p.y() <= in_pos.y()]
        # filter the cursor of 'y > pos'
        cursorBases = [(i, p) for i, p in cursorBases if cursorBases[-1][1].y() == p.y()]
        # find left < x < right
        left = next(((i, p) for i, p in cursorBases if p.x() + 5 >= pos.x()), None)
        if left:
            return item.ast(), left[0]
        elif len(cursorBases):
            return item.ast(), cursorBases[-1][0]
        else:
            return None, None
