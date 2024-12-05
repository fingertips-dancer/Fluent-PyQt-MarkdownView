import time
import typing as t

from PyQt5.QtCore import Qt, QPointF, QRect, QMargins, QRectF, QSizeF
from PyQt5.QtGui import QFontMetrics, QColor
from PyQt5.QtGui import QPainter, QPaintEvent, QMouseEvent, QKeyEvent, QInputMethodEvent, QKeySequence
from PyQt5.QtWidgets import QAction, QApplication, QVBoxLayout, QWidget, QScrollArea, QSpacerItem, QSizePolicy
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import RoundMenu, Action
from qfluentwidgets import SmoothScrollDelegate
from qfluentwidgets import ThemeColor

from . import render_function
from .cache_paint import CachePaint
from .component import ContentItem
from .component import PreEdit
from .cursor import MarkdownCursor
from .document import MarkDownDocument
from .markdown_ast import MarkdownASTBase
from .style import MarkdownStyle

render_function = render_function
MOVE_MODE = {Qt.Key_Up: MarkdownCursor.MOVE_UP,
             Qt.Key_Down: MarkdownCursor.MOVE_DOWN,
             Qt.Key_Left: MarkdownCursor.MOVE_FELT,
             Qt.Key_Right: MarkdownCursor.MOVE_RIGHT}


class MarkdownEdit(QScrollArea):
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

    def createContentItem(self, ast) -> ContentItem:
        _item = ContentItem(parent=self, cachePaint=self._cachePaint, ast=ast)
        _item.collapseRequested.connect(self.onCollapseRequestedEvent)
        self.__contentItems[ast] = _item
        return _item

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
        # marigin
        self._margins = QMargins(45, 25, 25, 25)
        # cursor
        self._cursor = MarkdownCursor(self)
        self._cursor._cachePaint = self._cachePaint
        self._cursor.showCursorShaderTimer.timeout.connect(self.viewport().update)
        # ast render pos
        self._ast_render_pos = {}
        # pre edit and cursor in this
        self._preEdit = PreEdit(self)
        # pre edit
        self.__style = MarkdownStyle()
        # items
        self.__contentItems: t.Dict[MarkdownASTBase, ContentItem] = {}

        self.__w = QWidget(self)
        self.setWidget(self.__w)
        self.mainLayout = QVBoxLayout(self.__w)
        self.itemLayout = QVBoxLayout()
        self.mainLayout.addLayout(self.itemLayout)
        self.mainLayout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.setViewportMargins(0, 0, 0, 0)
        self.setWidgetResizable(True)
        self.viewport().setStyleSheet("background-color:transparent;")

        # menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)

        # Ctrl + V
        self.paste_action = QAction(self)
        self.paste_action.setObjectName('action_paste')
        self.paste_action.triggered.connect(self.pasteFromClipboard)
        self.paste_action.setShortcut(QKeySequence(QKeySequence.Paste))
        self.paste_action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        self.addAction(self.paste_action)

        self.setMarkdown("")
        self.verticalScrollBar().valueChanged.connect(self.update)

    def setMarkdown(self, text: str) -> None:

        self.__document.setMarkdown(text)

        self.cursor().setAST(self.document().ast().children[0])
        self.cursor().setPos(0)
        self.updateMarkdownItem()

    def show_menu(self, pos):
        self.__menu = RoundMenu(self)
        self.__menu.addAction(Action(FIF.COPY, self.tr("复制"), triggered=lambda: self.save("stress.md")))
        self.__menu.addAction(Action(FIF.PASTE, self.tr("粘贴"), triggered=self.pasteFromClipboard))
        self.__menu.addAction(Action(FIF.SAVE, self.tr("保存"), triggered=lambda: self.save("stress.md")))
        self.__menu.exec_(self.mapToGlobal(pos))

    def save(self, path):
        text = self.__document.toMarkdown()
        print(self.__document.ast().summary())
        with open(path, "w") as f:
            f.write(text)

    def pasteFromClipboard(self):
        """ paste form clipboard """
        clipboard, cursor = QApplication.clipboard(), self.cursor()
        cursor.swapSelectionContent(text=str(clipboard.text()))
        self.update()

    def copyToClipboard(self):
        """ copy to clipboard """
        # 设置剪贴板文本
        clipboard = QApplication.clipboard()
        start_ast, start_pos, end_ast, end_pos = self.cursor().selectedASTs()
        start_idx = self.document().ast().index(start_ast)
        # get copy text
        copy_text = ""
        for ast in self.document().ast().children[start_idx:]:
            if ast is end_ast:
                copy_text += ast.toMarkdown()[:end_pos]
                break
            else:
                copy_text += ast.toMarkdown()
        copy_text = copy_text[start_pos:]
        clipboard.setText(copy_text)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        super(MarkdownEdit, self).paintEvent(event)
        st = time.time()
        # 1. draw rect
        rect = self.viewport().geometry()
        rect.moveTo(0, self.verticalScrollBar().value())

        # 2. 从缓存中获取图片绘制
        # 2. 不要viewport内的跳过
        y = 0  # self._margins.top()
        painter = QPainter(self.viewport())
        painter.translate(-rect.x(), -rect.y())

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
                bs = self._cachePaint.cursorPluginBases(ast=ast)
                _si = start_pos if ast is start_ast else 0
                _ei = end_pos if ast is end_ast else len(bs)
                if _ei - _si < 1: continue
                radius, bs = 5, bs[_si:_ei + 1]
                if len(bs) <= 1: continue
                rect_x = bs[0].x()
                for i, (b, nb) in enumerate(zip(bs[:-1], bs[1:])):
                    if b.y() != nb.y():
                        lineHeight = self._cachePaint.lineHeight(ast=ast, pos=i + _si)
                        painter.drawRoundedRect(QRectF(QPointF(rect_x, b.y() + self.__contentItems[ast].y()),
                                                       QSizeF(b.x() - rect_x, lineHeight)),
                                                radius, radius)
                        ph = self._cachePaint.textParagraphs(ast=ast, pos=i + _si)
                        rect_x = ph.indentation() + ph.margins().left()
                else:
                    lineHeight = self._cachePaint.lineHeight(ast=ast, pos=i + _si)
                    painter.drawRoundedRect(
                        QRectF(QPointF(rect_x, b.y() + self.__contentItems[ast].y()),
                               QSizeF(nb.x() - rect_x, lineHeight)), radius, radius)

        # 4. paint predit
        lineHeight = self._cachePaint.lineHeight(ast=self.cursor().ast(), pos=self.cursor().pos())
        pulginBasePos = self._cachePaint.cursorPluginBases(ast=self.cursor().ast(), pos=self.cursor().pos())
        pulginBasePos = pulginBasePos + QPointF(0, self.__contentItems[self.cursor().ast()].y())
        if self._preEdit.preeditText() != "":
            font = self.__style.hintFont(font=painter.font(), ast="paragraph")
            font.setPixelSize(lineHeight)
            fm = QFontMetrics(font)
            pen = painter.pen()
            # draw preedit rect
            painter.setPen(Qt.NoPen)
            painter.setOpacity(1)
            painter.setBrush(QColor(225, 225, 225))
            rect = fm.boundingRect(self._preEdit.preeditText())
            rect.moveTo(pulginBasePos.toPoint())
            painter.drawRoundedRect(rect, 5, 5)
            painter.setFont(font)
            painter.setPen(pen)
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
                painter.drawLine(pulginBasePos,
                                 QPointF(pulginBasePos.x(), pulginBasePos.y() + lineHeight))

        # print("绘制时间",self.verticalScrollBar().value(),time.time()-st)

    def updateMarkdownItem(self, asts: t.Union[t.List[MarkdownASTBase], MarkdownASTBase] = None):
        """
        渲染到缓存
        :param asts: 确定重绘的范围,None表示全部
        :return:
        """

        s, e = False, False
        for i, ast in enumerate(self.document().ast().children):
            if i + 1 > self.itemLayout.count():
                self.itemLayout.insertWidget(i, self.createContentItem(ast=ast))
                QApplication.instance().processEvents()
                continue

            item: ContentItem = self.itemLayout.itemAt(i).widget()
            if item.ast() is ast:
                if s: break
            else:
                self.itemLayout.removeWidget(item)
                item.hide()
                item.deleteLater()
                self.itemLayout.insertWidget(i, self.createContentItem(ast=ast))
                QApplication.instance().processEvents()
        # pop item
        for i in range(len(self.document().ast().children),
                       max(self.itemLayout.count(), len(self.document().ast().children))):
            QApplication.instance().processEvents()
            self.itemLayout.itemAt(i).widget().deleteLater()

    def mousePressEvent(self, e: QMouseEvent) -> None:
        # super(MarkdownEdit, self).mousePressEvent(e)
        # 点击移动 光标
        old_ast = self.cursor().ast()
        cursor = self.cursor()
        view_pos = e.pos() + QPointF(0, self.verticalScrollBar().value())
        cursor_pos = self._cachePaint.cursorPluginBases(ast=self.cursor().ast(), pos=self.cursor().pos())
        cursor_pos = cursor_pos + QPointF(0, self.__contentItems[self.cursor().ast()].y())
        cursor.move(flag=MarkdownCursor.MOVE_MOUSE, pos=view_pos - cursor_pos)
        cursor.setSelectMode(mode=cursor.SELECT_MODE_SINGLE)
        cursor.setIsShowCursorShader(True)
        self.__contentItems[old_ast].reset()
        self.__contentItems[self.cursor().ast()].reset()

        self.viewport().update()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        # 多选模式
        if e.buttons() == Qt.LeftButton:
            cursor = self.cursor()
            if cursor.selectMode() != cursor.SELECT_MODE_MUTIL: cursor.setSelectMode(cursor.SELECT_MODE_MUTIL)
            view_pos = e.pos() + QPointF(0, self.verticalScrollBar().value())
            cursor_pos = self._cachePaint.cursorPluginBases(ast=self.cursor().ast(), pos=self.cursor().pos())
            cursor_pos = cursor_pos + QPointF(0, self.__contentItems[self.cursor().ast()].y())

            cursor.move(flag=MarkdownCursor.MOVE_MOUSE,
                        pos=view_pos - cursor_pos)
            cursor.setIsShowCursorShader(True)
            self.viewport().update()

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        pass

    def inputMethodEvent(self, event: QInputMethodEvent) -> None:
        """输入法输入"""
        # 获取当前的候选词
        commitString = event.commitString()
        if commitString != "":
            self.cursor().add(event.commitString())
        self.updateMarkdownItem()
        self.viewport().update()

    def inputMethodQuery(self, property: Qt.InputMethodQuery) -> t.Any:
        # 获取当前输入法的状态
        if property == Qt.ImCursorRectangle:
            # 返回输入法候选框的位置
            pos = self._cachePaint.cursorPluginBases(ast=self.cursor().ast(), pos=self.cursor().pos())
            pos = pos + QPointF(0, self.__contentItems[self.cursor().ast()].y())
            h = self._cachePaint.lineHeight(ast=self.cursor().ast(), pos=self.cursor().pos())
            # 在光标下方显示候选框
            return QRect(pos.toPoint(), QSizeF(pos.x(), h).toSize())  # 100 是候选框的高度
        elif property == Qt.ImCursorPosition:
            return 0
        elif property == Qt.ImhHiddenText:
            return True
        self.updateMarkdownItem()
        return super().inputMethodQuery(property)

    def onCollapseRequestedEvent(self, item: ContentItem):
        """ on collpose requested event """
        root = self.document().ast()
        for ast in root.children[root.index(item.ast()) + 1:]:
            if ast.isShowCollapseButton():
                return
            self.__contentItems[ast].setVisible(not item.isCollapse())

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
            cursor.move(MOVE_MODE[e.key()])
            cursor.setIsShowCursorShader(True)
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
        else:
            # Convert the key to a character based on Shift and Caps Lock status
            if Qt.Key_9 >= e.key() >= Qt.Key_0:  # Numbers 0-9
                char = str(e.key() - Qt.Key_0)  # Convert to string
            elif Qt.Key_Z >= e.key() >= Qt.Key_A:  # Letters A-Z
                # Shift pressed and Caps Lock off or vice versa
                # Both pressed or neither
                char = e.text().upper() if isShiftPressed != isCapsLockOn else e.text().lower()
            else:
                # Handle special characters
                char = self.special_chars.get(e.key(), e.text())
                if not isShiftPressed:
                    # Handle non-shifted versions of special characters
                    char = char.lower() if char.isalpha() else e.text()
            # 添加
            if char:
                self.cursor().add(char)
            print(char)

        # update ast render
        # if input some new content, the ast will update near the ast of cursor
        ast_idx = self.document().ast().index(self.cursor().ast())
        self.updateMarkdownItem()
        for ast in self.document().ast().children[max(0, ast_idx - 3):ast_idx + 3]:
            self.__contentItems[ast].reset()
        self.viewport().update()

        # 观察是否在view中
        # 调整
        QApplication.instance().processEvents()  # <---先处理一次事件,获取响应的rect,不然输入事件会不同步
        # 获取 cusor 所在 的ast,以及对应的rect
        pos = self._cachePaint.cursorPluginBases(ast=self.cursor().ast(), pos=self.cursor().pos())
        y = pos.y() + self.__contentItems[self.cursor().ast()].y()
        lineHeight = self._cachePaint.lineHeight(ast=self.cursor().ast(), pos=self.cursor().pos())
        if y < self.verticalScrollBar().value():
            self.verticalScrollBar().setValue(int(y))
        elif y + lineHeight > self.verticalScrollBar().value() + self.viewport().height():
            self.verticalScrollBar().setValue(int(y + lineHeight - self.viewport().height()))

    def document(self) -> MarkDownDocument:
        return self.__document

    def cursor(self) -> MarkdownCursor:
        return self._cursor
