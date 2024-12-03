import time
import typing as t

from PyQt5.QtCore import Qt, QPointF, QRect, QMargins, QRectF, QSizeF
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtGui import QPainter, QPaintEvent, QMouseEvent, QKeyEvent, QInputMethodEvent, QKeySequence, QPixmap
from PyQt5.QtWidgets import QTextEdit, QApplication, QAction
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import RoundMenu, Action
from qfluentwidgets import SmoothScrollDelegate
from qfluentwidgets import ThemeColor

from . import render_function
from .cache_paint import CachePaint
from .component import MarkdownStyle
from .cursor import MarkdownCursor
from .document import MarkDownDocument

render_function = render_function
MOVE_MODE = {Qt.Key_Up: MarkdownCursor.MOVE_UP,
             Qt.Key_Down: MarkdownCursor.MOVE_DOWN,
             Qt.Key_Left: MarkdownCursor.MOVE_FELT,
             Qt.Key_Right: MarkdownCursor.MOVE_RIGHT}


class MarkdownEdit(QTextEdit):
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

    def __init__(self):
        super().__init__()
        self.setAcceptRichText(False)
        self.scrollDelegate = SmoothScrollDelegate(self)
        self.__document = MarkDownDocument()

        self.verticalScrollBar().setMaximum(1024)
        # cache
        self._cachePaint = CachePaint(self)
        # marigin
        self._margins = QMargins(5, 5, 5, 5)
        # cursor
        self._cursor = MarkdownCursor(self)
        self._cursor._cachePaint = self._cachePaint
        self._cursor.showCursorShaderTimer.timeout.connect(self.viewport().update)
        # ast render pos
        self._ast_render_pos = {}
        # pre edit
        self.__preeditText = ""
        # pre edit
        self.__style = MarkdownStyle()

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        self.__document.heightChanged.connect(self.onTextHeightChanged)

        # Ctrl + V
        self.paste_action = QAction(self)
        self.paste_action.setObjectName('action_paste')
        self.paste_action.triggered.connect(self.pasteFromClipboard)
        self.paste_action.setShortcut(QKeySequence(QKeySequence.Paste))
        self.paste_action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        self.addAction(self.paste_action)

        self.setMarkdown("")

    def setMarkdown(self, text: str) -> None:
        self.__document.setMarkdown(text)
        self.cursor().setAST(self.document().ast().children[0])
        self.cursor().setPos(0)
        self.renderMarkdownToCache()  # <--- paint

    def show_menu(self, pos):
        menu = RoundMenu(self)
        menu.addAction(Action(FIF.COPY, self.tr("复制"), triggered=lambda: self.save("1.md")))
        menu.addAction(Action(FIF.PASTE, self.tr("粘贴"), triggered=self.pasteFromClipboard))
        menu.addAction(Action(FIF.SAVE, self.tr("保存"), triggered=lambda: self.save("1.md")))
        menu.exec_(self.mapToGlobal(pos))

    def save(self, path):
        text = self.__document.toMarkdown()
        print(self.__document.markdownAst.summary())
        with open(path, "w") as f:
            f.write(text)

    def pasteFromClipboard(self):
        """ paste form clipboard """
        clipboard, cursor = QApplication.clipboard(), self.document().cursor()
        cursor.swapSelectionContent(text=str(clipboard.text()))
        self.update()

    def copyToClipboard(self):
        """ copy to clipboard """
        # 设置剪贴板文本
        clipboard = QApplication.clipboard()
        start_ast, start_pos, end_ast, end_pos = self.document().cursor().selectedASTs()
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
        # super(MarkdownEdit, self).paintEvent(event)
        st = time.time()

        rect = self.viewport().geometry()
        rect.moveTo(0, self.verticalScrollBar().value())

        # 2. 从缓存中获取图片绘制
        # 2. 不要viewport内的跳过
        y = 0
        painter = QPainter(self.viewport())
        painter.translate(-rect.x(), -rect.y())
        cachePxiamp = self._cachePaint.cachePxiamp()
        for ast in self.document().ast().children:
            pm = cachePxiamp[ast]
            self._ast_render_pos[ast] = y
            painter.drawPixmap(0, y, pm)
            y += pm.height()

        self._cachePaint.setPainter(painter=painter)
        # self._cachePaint.renderCursor(cursor=self.cursor())

        # paint cursor
        if self.cursor().isShowCursorShader():
            lineHeight = self._cachePaint.lineHeight(ast=self.cursor().ast(), pos=self.cursor().pos())
            pulginBasePos = self._cachePaint.cursorPluginBases(ast=self.cursor().ast(), pos=self.cursor().pos())
            pulginBasePos = pulginBasePos + QPointF(0, self._ast_render_pos[self.cursor().ast()])
            painter.drawLine(pulginBasePos, QPointF(pulginBasePos.x(), pulginBasePos.y() + lineHeight))
        # paint select content
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
                        painter.drawRoundedRect(QRectF(QPointF(rect_x, b.y() + self._ast_render_pos[ast]),
                                                       QSizeF(b.x() - rect_x, lineHeight)),
                                                radius, radius)
                        rect_x = self._cachePaint.indentation(ast, pos=i + _si)
                else:
                    lineHeight = self._cachePaint.lineHeight(ast=ast, pos=i + _si)
                    painter.drawRoundedRect(QRectF(QPointF(rect_x, b.y() + self._ast_render_pos[ast]),
                                                   QSizeF(nb.x() - rect_x, lineHeight)), radius, radius)
        if self.__preeditText != "":
            font = self.__style.hintFont(font=painter.font(), ast="paragraph")
            fm = QFontMetrics(font)
            # rect = fm.boundingRect(text=self.__preeditText)
            painter.setFont(font)
            pos = self._cachePaint.cursorPluginBases(ast=self.cursor().ast(), pos=self.cursor().pos())
            lineHeight = self._cachePaint.lineHeight(ast=self.cursor().ast(), pos=self.cursor().pos())
            pos = pos + QPointF(0, self._ast_render_pos[self.cursor().ast()] + lineHeight - fm.descent())  # <-- 考虑偏移
            painter.drawText(pos, self.__preeditText)

        painter.end()
        # print("t", time.time() - st)

    def renderMarkdownToCache(self):
        """ 渲染到缓存"""
        temp = QPixmap(10, 10)
        painter = QPainter(temp)
        # 绘制缓存
        self._cachePaint.setPainter(painter)
        self._cachePaint.setPaperWidth(self.viewport().width())
        self._cachePaint.setMargins(self._margins)
        self._cachePaint.setLeftEdge(self._margins.left())
        self._cachePaint.reset()
        self._cachePaint.newParagraph()  # 重置段落

        # 渲染登记
        self.document().ast().render(ht=self._cachePaint, style=MarkdownStyle(), cursor=self.cursor())
        painter.end()
        del temp, painter
        self._cachePaint.setPainter(None)
        self._cachePaint.render()

        # 计算需要的 verticalScroll
        self.verticalScrollBar().setMaximum(
            int(max(self.viewport().height(), self._cachePaint.height() - self.viewport().height() + 1)))
        return

    def resizeEvent(self, event) -> None:
        super(MarkdownEdit, self).resizeEvent(event)
        # 1.重回markdown
        self.renderMarkdownToCache()
        self.verticalScrollBar().setMaximum(
            int(max(self.viewport().height(), self._cachePaint.height() - self.viewport().height() + 1)))

    def onTextHeightChanged(self):
        """ 高度变化 """
        self.verticalScrollBar().setMaximum(
            int(max(self.viewport().height(), self._cachePaint.height() - self.viewport().height() + 1)))

    def mousePressEvent(self, e: QMouseEvent) -> None:
        # super(MarkdownEdit, self).mousePressEvent(e)
        # 点击移动 光标
        cursor = self.cursor()
        view_pos = e.pos() + QPointF(0, self.verticalScrollBar().value())
        cursor_pos = self._cachePaint.cursorPluginBases(ast=self.cursor().ast(), pos=self.cursor().pos())
        cursor_pos = cursor_pos + QPointF(0, self._ast_render_pos[self.cursor().ast()])
        cursor.move(flag=MarkdownCursor.MOVE_MOUSE,
                    pos=view_pos - cursor_pos)
        cursor.setSelectMode(mode=cursor.SELECT_MODE_SINGLE)
        cursor.setIsShowCursorShader(True)
        self.viewport().update()
        self.renderMarkdownToCache()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        # 多选模式
        if e.buttons() == Qt.LeftButton:
            cursor = self.cursor()
            if cursor.selectMode() != cursor.SELECT_MODE_MUTIL: cursor.setSelectMode(cursor.SELECT_MODE_MUTIL)
            view_pos = e.pos() + QPointF(0, self.verticalScrollBar().value())
            cursor_pos = self._cachePaint.cursorPluginBases(ast=self.cursor().ast(), pos=self.cursor().pos())
            cursor_pos = cursor_pos + QPointF(0, self._ast_render_pos[self.cursor().ast()])

            cursor.move(flag=MarkdownCursor.MOVE_MOUSE,
                        pos=view_pos - cursor_pos)
            cursor.setIsShowCursorShader(True)
            self.viewport().update()

    def mouseReleaseEventEvent(self, e: QMouseEvent) -> None:
        # 退出多选
        cursor = self.cursor()
        cursor.setSelectMode(cursor.SELECT_MODE_SINGLE)
        self.viewport().update()

    def inputMethodEvent(self, event: QInputMethodEvent) -> None:
        """输入法输入"""
        # 获取当前的候选词
        commitString = event.commitString()
        if commitString != "":
            self.cursor().add(event.commitString())
            self.__preeditText = ""
        else:
            self.__preeditText = event.preeditString()  # 获取未最终确定的输入内容
        self.renderMarkdownToCache()
        self.viewport().update()

    def inputMethodQuery(self, property: Qt.InputMethodQuery) -> t.Any:
        # 获取当前输入法的状态
        if property == Qt.ImCursorRectangle:
            # 返回输入法候选框的位置
            pos = self._cachePaint.cursorPluginBases(ast=self.cursor().ast(), pos=self.cursor().pos())
            pos = pos + QPointF(0,
                                self._ast_render_pos[self.cursor().ast()] + \
                                self._cachePaint.lineHeight(ast=self.cursor().ast(), pos=self.cursor().pos()))
            # 在光标下方显示候选框
            return QRect(pos.toPoint(), QSizeF(pos.x(), 1).toSize())  # 100 是候选框的高度
        self.renderMarkdownToCache()
        return super().inputMethodQuery(property)

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
        self.renderMarkdownToCache()
        self.viewport().update()

        # 观察是否在view中
        # 调整
        QApplication.instance().processEvents()  # <---先处理一次事件,获取响应的rect,不然输入事件会不同步
        # 获取 cusor 所在 的ast,以及对应的rect
        pos = self._cachePaint.cursorPluginBases(ast=self.cursor().ast(), pos=self.cursor().pos())
        y = pos.y() + self._ast_render_pos[self.cursor().ast()]
        lineHeight = self._cachePaint.lineHeight(ast=self.cursor().ast(), pos=self.cursor().pos())
        if y < self.verticalScrollBar().value():
            self.verticalScrollBar().setValue(int(y))
        elif y + lineHeight > self.verticalScrollBar().value() + self.viewport().height():
            self.verticalScrollBar().setValue(int(y + lineHeight - self.viewport().height()))

    def document(self) -> MarkDownDocument:
        return self.__document

    def cursor(self) -> MarkdownCursor:
        return self._cursor
