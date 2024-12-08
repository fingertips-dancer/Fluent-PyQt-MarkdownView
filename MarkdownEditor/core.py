import os
import time
import typing as t

from PyQt5.QtCore import Qt, QPointF, QRect, QMargins, QRectF, QSizeF, QTimer, QPoint
from PyQt5.QtGui import QFontMetrics, QColor
from PyQt5.QtGui import QPainter, QPaintEvent, QMouseEvent, QKeyEvent, QInputMethodEvent, QKeySequence
from PyQt5.QtWidgets import QAction, QApplication, QScrollArea
from qfluentwidgets import Action
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SmoothScrollDelegate, RoundMenu
from qfluentwidgets import ThemeColor

from . import render_function
from .abstruct import AbstractMarkdownEdit
from .cache_paint import CachePaint
from .component import ContentItem, Container
from .component import PreEdit, LoadProgressBar
from .cursor import MarkdownCursor
from .document import MarkDownDocument
from .markdown_ast import MarkdownASTBase
from .style import MarkdownStyle

render_function = render_function
MOVE_MODE = {Qt.Key_Up: MarkdownCursor.MOVE_UP,
             Qt.Key_Down: MarkdownCursor.MOVE_DOWN,
             Qt.Key_Left: MarkdownCursor.MOVE_FELT,
             Qt.Key_Right: MarkdownCursor.MOVE_RIGHT}
special_chars = {
    Qt.Key_1: '!',
    Qt.Key_2: '@',
    Qt.Key_3: '#',
    Qt.Key_4: '$',
    Qt.Key_5: '%',
    Qt.Key_6: '^',
    Qt.Key_7: '&',
    Qt.Key_8: '*',
    Qt.Key_9: '(',
    Qt.Key_0: ')',
    Qt.Key_Minus: '_',
    Qt.Key_Equal: '+',
    Qt.Key_BracketLeft: '{',
    Qt.Key_BracketRight: '}',
    Qt.Key_Semicolon: ':',
    Qt.Key_Apostrophe: '"',
    Qt.Key_Comma: '<',
    Qt.Key_Period: '>',
    Qt.Key_Slash: '?'
}


class MarkdownEdit(QScrollArea, AbstractMarkdownEdit):
    def createContentItem(self, ast) -> ContentItem:
        _item = ContentItem(parent=self, cachePaint=self._cachePaint, ast=ast)
        _item.collapseRequested.connect(self.onCollapseRequestedEvent)
        _item.setParent(self.__w)
        self.__contentItems[ast] = _item
        return _item

    def _adjustScroll(self):
        if len(self.__contentItems.values()):
            item = list(self.__contentItems.values())[-1]
            while item.downItem():
                item = item.downItem()
            self.__w.setFixedHeight((item.y() + item.height()))

    def autoUpdateMarkdownItem(self, maxUpdateNum=10, updatesEnabled=True):
        """
        渲染到缓存
        :param asts: 确定重绘的范围,None表示全部
        :return:
        """
        self.setUpdatesEnabled(False)  # <--禁止重绘,防止闪烁
        # 使用缓存来绘制
        self.__updateItemer.stop()

        # 删除多余的item
        have_init_items = set(self.__contentItems.keys())
        need_init_items = set(self.document().ast().children)
        need_del_items = have_init_items.difference(need_init_items)
        if len(need_del_items):
            self.loadProgressBar.show()
            self.loadProgressBar.setMaximum(len(need_del_items))
            for i, ast in enumerate(need_del_items):
                self.loadProgressBar.setValue(i + 1)
                item = self.__contentItems.pop(ast)
                item.hide()
                item.deleteLater()

        # 差集,查看需要初始化的item
        # 需要保持顺序
        not_init_items = [ast for ast in self.document().ast().children if ast not in have_init_items]
        # 初始化
        _len = len(not_init_items)
        if _len:
            the_len = len(self.document().ast().children) - 1
            self.loadProgressBar.setMaximum(the_len)
            for i, ast in enumerate(not_init_items[:maxUpdateNum]):
                self.loadProgressBar.setValue(the_len - _len + i + 1)
                item = self.createContentItem(ast=ast)
                item.setFixedWidth(self.width())
                self.__contentItems[ast] = item
                upAst = ast.upAst()
                downAst = ast.downAst()
                if upAst in self.__contentItems: item.setUpItem(self.__contentItems[upAst])
                if downAst in self.__contentItems: item.setDownItem(self.__contentItems[downAst])
                item.show()

        # move item
        # up or down for self.height()
        item: ContentItem = self.__w.childAt(self.width() // 2,
                                             max(0, self.verticalScrollBar().value() - self.height() * 2))
        while item is not None and item.y() - self.verticalScrollBar().value() < self.height() * 2:
            if item.upItem():
                item.move(0, item.upItem().y() + item.upItem().height())
            item = item.downItem()

        startIime = time.time()
        self.__is_use_view_render_cache = False
        self.__updateItemer.start(10)
        self.loadProgressBar.hide()
        self._adjustScroll()
        self.setUpdatesEnabled(True)  # <--重绘,防止闪烁
        self.repaint()

    def __init__(self):
        super().__init__()
        # 允许输入法
        self.setAttribute(Qt.WA_InputMethodEnabled, True)
        # self.setAcceptRichText(False)
        self.scrollDelegate = SmoothScrollDelegate(self)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # document
        self.__document = MarkDownDocument()
        # cache
        self._cachePaint = CachePaint(self)
        # cursor
        self._cursor = MarkdownCursor(self)
        self._cursor.showCursorShaderTimer.timeout.connect(self.viewport().update)
        # pre edit and cursor in this
        self._preEdit = PreEdit(self)
        # pre edit
        # items
        self.__contentItems: t.Dict[MarkdownASTBase, ContentItem] = {}

        # widget
        self.loadProgressBar = LoadProgressBar(self)
        self.loadProgressBar.show()
        self.__w = Container(self)
        self.setWidget(self.__w)
        self.setWidgetResizable(True)
        self.viewport().setStyleSheet("background-color:transparent;")

        # menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

        # Ctrl + V
        self.paste_action = QAction(self)
        self.paste_action.setObjectName('action_paste')
        self.paste_action.triggered.connect(self.pasteFromClipboard)
        self.paste_action.setShortcut(QKeySequence(QKeySequence.Paste))
        self.paste_action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        self.addAction(self.paste_action)

        # connect
        self.verticalScrollBar().valueChanged.connect(self.onScrollValueChangedEvent)
        self.verticalScrollBar().valueChanged.connect(self.update)
        # auto update
        self.__updateItemer = QTimer()
        self.__updateItemer.setSingleShot(True)
        self.__updateItemer.timeout.connect(self.autoUpdateMarkdownItem)

        # init
        self.setSytle()
        self.setMarkdown("")
        self.__updateItemer.start(10)

    def setSytle(self, style: str = None) -> None:
        path = os.path.join(os.path.dirname(__file__), "_rc", "github.css") if style is None else style
        with open(path, 'r', encoding="utf8") as f:
            css_content = f.read()
        self.__style = MarkdownStyle.create(css_content)

        margins = self.__style.hintBackgroundMargins(ast='root')
        self._margins = QMargins(*margins)

    def setMarkdown(self, text: str) -> None:
        self.__document.setMarkdown(text)
        self.cursor().setSelectMode(mode=MarkdownCursor.SELECT_MODE_SINGLE)
        self.cursor().setAST(self.document().ast().children[0])
        self.cursor().setPos(0)
        self.autoUpdateMarkdownItem()

    def _show_menu(self, pos) -> None:
        self.__menu = RoundMenu(self)
        self.__menu.addAction(Action(FIF.COPY, self.tr("复制"), triggered=self.copyToClipboard))
        self.__menu.addAction(Action(FIF.PASTE, self.tr("粘贴"), triggered=self.pasteFromClipboard))
        sub_menu = RoundMenu("添加")
        sub_menu.addAction(Action(FIF.COPY, self.tr("图片"), triggered=lambda: print("图片")))
        sub_menu.addAction(Action(FIF.COPY, self.tr("公式"), triggered=lambda: print("公式")))
        sub_menu.addAction(Action(FIF.COPY, self.tr("连接"), triggered=lambda: print("连接")))
        sub_menu.addAction(Action(FIF.COPY, self.tr("连接"), triggered=lambda: print("表格")))
        sub_menu.setIcon(FIF.ADD)
        self.__menu.addMenu(sub_menu)
        self.__menu.exec_(self.mapToGlobal(pos))

    def _moveViewToCurosr(self) -> None:
        """ change the value of verticalScrollBar to show cursor """
        y = self.cursorBases(ast=self.cursor().ast(), pos=self.cursor().pos()).y()
        lineHeight = self.__contentItems[self.cursor().ast()].lineHeight(pos=self.cursor().pos())
        if y < self.verticalScrollBar().value():
            self.verticalScrollBar().setValue(int(y))
        elif y + lineHeight > self.verticalScrollBar().value() + self.viewport().height():
            self.verticalScrollBar().setValue(int(y + lineHeight - self.viewport().height()))

    def pasteFromClipboard(self) -> None:
        """ paste form clipboard """
        clipboard, cursor = QApplication.clipboard(), self.cursor()
        cursor.swapSelectionContent(text=str(clipboard.text()))
        self.update()

    def copyToClipboard(self) -> None:
        """ copy to clipboard """
        # 设置剪贴板文本
        clipboard = QApplication.clipboard()
        start_ast, start_pos, end_ast, end_pos = self.cursor().selectedASTs()
        start_idx = self.document().ast().index(start_ast)
        end_idx = self.document().ast().index(end_ast)
        # get copy text
        copy_text = ""
        for ast in self.document().ast().children[start_idx:end_idx + 1]:
            copy_text += ast.toMarkdown()
        copy_text = copy_text[start_pos:end_pos - len(ast.toMarkdown())]
        clipboard.setText(copy_text)
        self.update()

    def cursorMoveTo(self, pos: t.Union[QPointF, QPoint]) -> None:
        """ overload """
        ast, pos = self.cursorBaseIn(pos=pos)
        if pos is not None:
            self.cursor().setAST(ast=ast, pos=pos)

    def paintEvent(self, event: QPaintEvent) -> None:
        if self.cursor().ast() not in self.__contentItems:
            return
        # super(MarkdownEdit, self).paintEvent(event)

        # 1. 从缓存中获取图片绘制
        # 1. 不要viewport内的跳过
        painter = QPainter(self.viewport())
        painter.translate(-0, -self.verticalScrollBar().value())

        # 3. paint select content
        start_ast, start_pos, end_ast, end_pos = self.cursor().selectedASTs()
        if not (start_ast is end_ast and start_pos == end_pos):  # 不在原地
            color = ThemeColor.PRIMARY.color()
            color.setAlpha(125)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            for ast_index in range(self.document().ast().children.index(start_ast),
                                   self.document().ast().children.index(end_ast) + 1):
                ast = self.document().ast().children[ast_index]
                if not self.__contentItems[ast].inViewport(): continue  # <--不再视图内,可以不显示
                bs = [(i, p) for i, p in enumerate(self.cursorBases(ast=ast))]
                _si = start_pos if ast is start_ast else 0
                _ei = end_pos if ast is end_ast else len(bs)
                if _ei - _si < 1: continue
                radius, bs = 5, bs[_si:_ei + 1]
                ys = {p.y() for p in self.cursorBases(ast=ast)[_si:_ei + 1]}
                if len(bs) <= 1: continue
                for y in ys:
                    left_i, left_p = min((i for i in bs if i[1].y() == y), key=lambda x: x[1].x())
                    right_i, right_p = max((i for i in bs if i[1].y() == y), key=lambda x: x[1].x())
                    lineHeight = self.__contentItems[ast].lineHeight(pos=left_i)
                    indentation = self.__contentItems[ast].indentation(pos=left_i)
                    left_x = left_p.x() if y == min(ys) else indentation + self._margins.left()
                    painter.drawRoundedRect(QRectF(QPointF(left_x, left_p.y()),
                                                   QSizeF(right_p.x() - left_x, lineHeight)),
                                            radius, radius)

        # 4. paint predit
        lineHeight = self.__contentItems[self.cursor().ast()].lineHeight(pos=self.cursor().pos())
        pulginBasePos = self.cursorBases(ast=self.cursor().ast(), pos=self.cursor().pos())
        if self._preEdit.preeditText() != "":
            font = self.__style.hintFont(font=painter.font(), ast="root")
            font.setPixelSize(int(lineHeight * 0.8))
            fm = QFontMetrics(font)
            painter.setFont(font)
            # draw preedit rect
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 255))
            rect = fm.boundingRect(self._preEdit.preeditText())
            rect.moveTo(pulginBasePos.toPoint())
            painter.drawRoundedRect(rect, 5, 5)
            painter.restore()
            # draw content
            painter.setFont(font)
            painter.drawText(QPointF(pulginBasePos.x(), pulginBasePos.y() + lineHeight - fm.descent()),
                             self._preEdit.preeditText())

        # 5.paint cursor
        if self.cursor().isShowCursorShader():
            if self._preEdit.preeditText() == "":
                # paint cursor
                painter.drawLine(pulginBasePos, QPointF(pulginBasePos.x(), pulginBasePos.y() + lineHeight))
            else:
                # paint cursor in predit
                w = fm.width(self._preEdit.preeditText()[:self._preEdit.cursorPos()])
                pulginBasePos = pulginBasePos + QPointF(w, 0)
                painter.drawLine(pulginBasePos, QPointF(pulginBasePos.x(), pulginBasePos.y() + lineHeight))

    def onScrollValueChangedEvent(self, value: int) -> None:
        """ onScrollValueChangedEvent """
        item: ContentItem = self.__w.childAt(self.width() // 2, value)
        if item and item.ast().downAst():
            self.__contentItems[item.ast().downAst()].render_()

    def mousePressEvent(self, e: QMouseEvent) -> None:
        # 左键点击移动 光标
        if e.button() == Qt.LeftButton:
            old_ast = self.cursor().ast()
            cursor = self.cursor()
            view_pos = e.pos() + QPointF(0, self.verticalScrollBar().value())
            cursor.move(flag=MarkdownCursor.MOVE_MOUSE, pos=view_pos)
            cursor.setSelectMode(mode=cursor.SELECT_MODE_SINGLE)
            cursor.setIsShowCursorShader(True)
            self.__contentItems[old_ast].reset()
            self.__contentItems[self.cursor().ast()].reset()
            self.viewport().update()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        view_pos = e.pos() + QPointF(0, self.verticalScrollBar().value())
        if e.buttons() == Qt.LeftButton:# 按下左键拖动
            old_ast = self.cursor().ast()
            cursor = self.cursor()
            if cursor.selectMode() != cursor.SELECT_MODE_MUTIL: cursor.setSelectMode(cursor.SELECT_MODE_MUTIL)
            cursor.move(flag=MarkdownCursor.MOVE_MOUSE, pos=view_pos)
            cursor.setIsShowCursorShader(True)
            self.__contentItems[old_ast].reset()
            self.__contentItems[self.cursor().ast()].reset()
            self.viewport().update()
        elif e.buttons() == Qt.NoButton:#<---没有点击
            ast, pos = self.cursorBaseIn(pos=view_pos)
        # 2. modify curosr style
        self.setCursor(Qt.IBeamCursor)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        pass

    def inputMethodEvent(self, event: QInputMethodEvent) -> None:
        """输入法输入"""
        # 获取当前的候选词
        commitString = event.commitString()
        if commitString != "":
            self.cursor().add(event.commitString())
            self.autoUpdateMarkdownItem(updatesEnabled=False)
            self._moveViewToCurosr()
        self.viewport().update()

    def inputMethodQuery(self, property: Qt.InputMethodQuery) -> t.Any:
        # 获取当前输入法的状态
        if property == Qt.ImCursorRectangle:
            # 返回输入法候选框的位置
            pos = self.cursorBases(ast=self.cursor().ast(), pos=self.cursor().pos())
            pos = pos + QPointF(0, self.__contentItems[self.cursor().ast()].y())
            h = self.__contentItems[self.cursor().ast()].lineHeight(pos=self.cursor().pos())
            # 在光标下方显示候选框
            return QRect(pos.toPoint(), QSizeF(pos.x(), h).toSize())  # 100 是候选框的高度
        # self.updateMarkdownItem(updating=False)
        return super().inputMethodQuery(property)

    def onCollapseRequestedEvent(self, item: ContentItem) -> None:
        """ on collpose requested event """
        root = self.document().ast()
        for ast in root.children[root.index(item.ast()) + 1:]:
            if ast.isShowCollapseButton(): return
            self.__contentItems[ast].hide() if item.isCollapse() else self.__contentItems[ast].show()
        self._adjustScroll()

    def resizeEvent(self, e) -> None:
        super(MarkdownEdit, self).resizeEvent(e)
        self._adjustScroll()

    def enterEvent(self, event) -> None:
        super(MarkdownEdit, self).enterEvent(event)
        # modify cusor style
        self.setCursor(Qt.IBeamCursor)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        # super(MarkdownEdit, self).keyPressEvent(e)
        # Check if Shift and Caps Lock are pressed
        isShiftPressed = e.modifiers() & Qt.ShiftModifier
        isCapsLockOn = QApplication.keyboardModifiers() & Qt.Key_CapsLock
        isCtrlPress = e.modifiers() & Qt.ControlModifier
        cursor = self.cursor()
        if e.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            # 判断光标多选还是单选
            if isShiftPressed and cursor.selectMode() != cursor.SELECT_MODE_MUTIL:
                cursor.setSelectMode(cursor.SELECT_MODE_MUTIL)
            elif not isShiftPressed:
                cursor.setSelectMode(cursor.SELECT_MODE_SINGLE)
            # 移动
            old_ast = self.cursor().ast()
            cursor.move(MOVE_MODE[e.key()])
            cursor.setIsShowCursorShader(True)
            self.__contentItems[old_ast].reset()
            self.__contentItems[self.cursor().ast()].reset()
            self.viewport().update()
        elif e.key() == Qt.Key_Backspace:  # 删除
            if cursor.selectMode() == cursor.SELECT_MODE_SINGLE:
                self.cursor().pop(_len=1)
            else:
                self.cursor().removeSelectionContent()
        elif e.key() == Qt.Key_Return:  # 回车
            self.cursor()._return()
        elif isCtrlPress:  # Ctrl
            if e.key() == Qt.Key_V:
                self.pasteFromClipboard()
            elif e.key() == Qt.Key_C:
                self.copyToClipboard()
        elif e.key() != Qt.Key_Escape:
            # Convert the key to a character based on Shift and Caps Lock status
            if Qt.Key_9 >= e.key() >= Qt.Key_0:  # Numbers 0-9
                char = str(e.key() - Qt.Key_0)  # Convert to string
            elif Qt.Key_Z >= e.key() >= Qt.Key_A:  # Letters A-Z
                # Shift pressed and Caps Lock off or vice versa
                # Both pressed or neither
                char = e.text().upper() if isShiftPressed != isCapsLockOn else e.text().lower()
            else:
                # Handle special characters
                char = special_chars.get(e.key(), e.text())
                if not isShiftPressed:
                    # Handle non-shifted versions of special characters
                    char = char.lower() if char.isalpha() else e.text()
            # 添加
            if char:
                self.cursor().add(char)
            print(char, e.key())
        # update ast render
        # if input some new content, the ast will update near the ast of cursor
        self.autoUpdateMarkdownItem(updatesEnabled=False)
        self.viewport().repaint()

        # 观察是否在view中
        # 获取 cusor 所在 的ast,以及对应的rect
        self._moveViewToCurosr()

    def document(self) -> MarkDownDocument:
        return self.__document

    def cursor(self) -> MarkdownCursor:
        return self._cursor

    def markdownStyle(self) -> MarkdownStyle:
        return self.__style

    def cursorBases(self, ast, pos: int = None) -> QPoint or t.List[QPoint]:
        item = self.__contentItems[ast]
        if pos is not None:
            return item.pos() + item.cursorBases()[pos]
        return [item.pos() + p for p in item.cursorBases()]

    def astIn(self, pos: QPoint) -> MarkdownASTBase:
        item = self.__w.childAt(pos)
        if not isinstance(item, ContentItem):
            return None
        return item.ast()

    def geometryOf(self, ast) -> QRect:
        return self.__contentItems[ast].geometry()

    def cursorBaseIn(self, pos: t.Union[QPointF, QPoint]) -> t.Optional[t.Tuple[MarkdownASTBase, int]]:
        """ overload """
        if isinstance(pos, QPointF): pos = pos.toPoint()
        item: ContentItem = self.__w.childAt(pos)
        if not isinstance(item, ContentItem): return
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
