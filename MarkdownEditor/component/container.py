import time
import typing as t

from PyQt5.QtCore import QRect, QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QScrollArea, QVBoxLayout

from .content_item import ContentItem
from ..abstruct import AbstractMarkdownEdit
from ..cache_paint import CachePaint
from ..document import MarkDownDocument
from ..markdown_ast import MarkdownASTBase


class Container(QWidget):
    itemCreated = pyqtSignal(ContentItem)

    def createContentItem(self, ast) -> ContentItem:
        _item = ContentItem(parent=self.area(), cachePaint=self._cachePaint, ast=ast)
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
                item = self.__contentItems.pop(ast)
                if ast in self.__nowShowAst: self.__nowShowAst.remove(ast)
                item.hide()
                item.deleteLater()

        # 差集,查看需要初始化的item
        # 需要保持顺序
        not_init_items = [ast for ast in self.document().ast().children if ast not in have_init_items]
        # 初始化
        _len = len(not_init_items)
        if _len:
            the_len = len(self.document().ast().children) - 1
            for i, ast in enumerate(not_init_items[:maxUpdateNum]):
                item = self.createContentItem(ast=ast)
                # item.setFixedWidth(self.width())
                self.__contentItems[ast] = item
                upAst = ast.upAst()
                downAst = ast.downAst()
                if upAst in self.__contentItems: item.setUpItem(self.__contentItems[upAst])
                if downAst in self.__contentItems: item.setDownItem(self.__contentItems[downAst])
                item.hide()
        st = time.time()
        self.updateShowLayout()
        # st = time.time()
        self.__updateItemer.start(10)
        self.setUpdatesEnabled(True)  # <--重绘,防止闪烁
        self.area().setUpdatesEnabled(True) # <--重绘,防止闪烁

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

        scrollValue = area.verticalScrollBar().value()
        # 1. when it have not item be show
        self.setUpdatesEnabled(False)  # <--禁止重绘,防止闪烁

        if len(self.__nowShowAst) == 0:
            item = self.__contentItems[self.document().ast().children[0]]
            self.preprocess(item, y=0)
            self.__nowShowAst.append(item.ast())
            h = self.height() - item.height()
            while h >= 0 and item.downItem():
                downItem = item.downItem()
                self.preprocess(downItem, y=item.geometry().bottom())
                self.__nowShowAst.append(downItem.ast())
                item = downItem
                h = h - item.height()

        else:
            c_item = self.__contentItems[self.__nowShowAst[0]]
            nowShowAst = [c_item.ast()]

            # up
            item = c_item
            thresh_y = c_item.geometry().y() - area.verticalScrollBar().value()
            while thresh_y >= -300 and item.upItem():
                upItem = item.upItem()
                self.preprocess(upItem, y=item.geometry().y())
                upItem.move(0, max(0, item.y() - upItem.height()))
                nowShowAst.insert(0, upItem.ast())
                item = upItem
                thresh_y = thresh_y - item.height()
            st = time.time()
            # down
            item = c_item
            thresh_y = area.verticalScrollBar().value() + area.height() - c_item.geometry().bottom()
            while thresh_y >= -300 and item.downItem():
                downItem = item.downItem()
                self.preprocess(downItem, y=item.geometry().bottom())
                nowShowAst.append(downItem.ast())
                item = downItem
                thresh_y = thresh_y - item.height()

            # hide
            need_hide_ast = set(self.__nowShowAst).difference(set(nowShowAst))
            for ast in need_hide_ast:
                self.__contentItems[ast].hide()

            # 重排保证一致
            if self.__contentItems[nowShowAst[0]].y() <= 0:
                for ast in nowShowAst[1:]:
                    item = self.__contentItems[ast]
                    item.move(0, item.upItem().geometry().bottom())

            # hide over up item
            for ast in nowShowAst.copy():
                if self.__contentItems[ast].geometry().bottom() < area.verticalScrollBar().value() - 100:
                    self.__contentItems[ast].hide()
                    nowShowAst.pop(0)
                else:
                    break
            self.__nowShowAst = nowShowAst
            # print("update11", time.time() - st)

        last_show_item = self.__contentItems[self.__nowShowAst[-1]]
        b = last_show_item.geometry().bottom()
        guess = max(self.__downW.geometry().bottom(), b + 20)  # <--不是最后一个
        guess = b if last_show_item.ast() is self.document().ast().children[-1] else guess
        self.__downW.setFixedHeight(0)
        self.__downW.move(0, guess)

        # self.__downW.move(0, last_show_item.geometry().bottom())
        self.setFixedHeight(max(self.__downW.geometry().bottom(), 0))
        self.setUpdatesEnabled(True)  # <--禁止重绘,防止闪烁
        # print("当前绘制", len(self.__nowShowAst), self.height(), area.viewport().height(), area.verticalScrollBar().value())

    def __init__(self, parent: AbstractMarkdownEdit):
        self.__area: AbstractMarkdownEdit or QScrollArea = parent
        self.__contentItems: t.Dict[MarkdownASTBase, ContentItem] = {}
        self._cachePaint = CachePaint(self)
        self.__yCache: t.Dict[MarkdownASTBase, QRect] = {}
        self.__nowShowAst: t.List[MarkdownASTBase] = []
        self.__needRerender = True
        super(Container, self).__init__(parent)
        self.__upW, self.__downW = QWidget(self), QWidget(self)
        self.setMouseTracking(True)  # 鼠标追踪

        self.wLayout = QVBoxLayout(self)
        self.wLayout.setContentsMargins(0, 0, 0, 0)

        self.itemLayout = QVBoxLayout()

        # self.wLayout.addWidget(self.__upW)
        # self.wLayout.addLayout(self.itemLayout)
        # self.wLayout.addWidget(self.__downW)
        self.__upW.show()
        self.__downW.show()
        self.itemLayout.setSpacing(0)
        self.wLayout.setSpacing(0)
        self.__upW.setFixedHeight(0)
        self.__downW.setFixedHeight(0)

        # auto update
        self.__updateItemer = QTimer()
        self.__updateItemer.setSingleShot(True)
        self.__updateItemer.timeout.connect(self.autoUpdateMarkdownItem)

    def area(self) -> t.Union[AbstractMarkdownEdit or QScrollArea]:
        return self.__area

    def contentItemCache(self) -> t.Dict[MarkdownASTBase, ContentItem]:
        return self.__contentItems

    def document(self) -> MarkDownDocument:
        return self.area().document()
