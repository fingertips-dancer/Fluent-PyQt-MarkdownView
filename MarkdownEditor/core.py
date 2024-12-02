import time
import typing as t

from PyQt5.QtCore import Qt, QPointF, QRect
from PyQt5.QtGui import QPainter, QPaintEvent, QMouseEvent, QKeyEvent, QInputMethodEvent, QKeySequence
from PyQt5.QtWidgets import QTextEdit, QApplication, QAction,QScrollArea
from qfluentwidgets import SmoothScrollDelegate
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import RoundMenu, Action

from .cursor import MarkdownCursor
from .document import MarkDownDocument

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
        self.__document.cursor().showCursorShaderTimer.timeout.connect(lambda: self.viewport().update())
        # self.setDocument(self.__document)
        self.verticalScrollBar().setMaximum(1024)

        self.pragh = None

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
        painter = QPainter(self.viewport())
        rect = self.viewport().geometry()
        rect.moveTo(0, self.verticalScrollBar().value())
        self.__document.render(painter=painter, rect=rect)
        print("t", time.time() - st)

    def resizeEvent(self, event) -> None:
        super(MarkdownEdit, self).resizeEvent(event)
        self.verticalScrollBar().setMaximum(
            int(max(self.viewport().height(), self.__document.height() - self.viewport().height() + 1)))
        self.__document.setViewportWidth(self.viewport().width())
        # print("resizeEvent", self.viewport().width())

    def onTextHeightChanged(self):
        """ 高度变化 """
        self.verticalScrollBar().setMaximum(
            int(max(self.viewport().height(), self.__document.height() - self.viewport().height() + 1)))

    def mousePressEvent(self, e: QMouseEvent) -> None:
        # super(MarkdownEdit, self).mousePressEvent(e)
        # 点击移动 光标
        cursor = self.__document.cursor()
        cursor.move(flag=MarkdownCursor.MOVE_MOUSE,
                    pos=e.pos() + QPointF(0, self.verticalScrollBar().value()))
        cursor.setSelectMode(mode=cursor.SELECT_MODE_SINGLE)
        cursor.setIsShowCursorShader(True)
        self.viewport().update()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        # 多选模式
        if e.buttons() == Qt.LeftButton:
            cursor = self.__document.cursor()
            if cursor.selectMode() != cursor.SELECT_MODE_MUTIL: cursor.setSelectMode(cursor.SELECT_MODE_MUTIL)
            cursor.move(flag=MarkdownCursor.MOVE_MOUSE, pos=e.pos() + QPointF(0, self.verticalScrollBar().value()))
            cursor.setIsShowCursorShader(True)
            self.viewport().update()

    def mouseReleaseEventEvent(self, e: QMouseEvent) -> None:
        # 退出多选
        cursor = self.__document.cursor()
        cursor.setSelectMode(cursor.SELECT_MODE_SINGLE)
        self.viewport().update()

    def inputMethodEvent(self, event: QInputMethodEvent) -> None:
        """输入法输入"""
        self.__document.cursor().add(event.commitString())
        self.viewport().update()

    def inputMethodQuery(self, property: Qt.InputMethodQuery) -> t.Any:
        if property == Qt.ImCursorRectangle and False:
            # 返回输入法候选框的位置
            rect = self.__document.cursor().rect().toRect()
            # 在光标下方显示候选框
            return QRect(rect.x(), rect.bottom(), rect.width(), 50)  # 100 是候选框的高度
        return super().inputMethodQuery(property)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        # super(MarkdownEdit, self).keyPressEvent(e)
        # Check if Shift and Caps Lock are pressed
        isShiftPressed = e.modifiers() & Qt.ShiftModifier
        isCapsLockOn = QApplication.keyboardModifiers() & Qt.Key_CapsLock
        isCtrlPress = e.modifiers() & Qt.ControlModifier
        cursor = self.__document.cursor()
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
                self.document().cursor().pop(_len=1)
            else:
                self.document().cursor().removeSelectionContent()
        elif e.key() == Qt.Key_Return:  # 回车
            self.document().cursor()._return()
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
            if char: self.__document.cursor().add(char)
            print(char)
        self.viewport().update()
        # 观察是否在view中
        # 调整
        QApplication.instance().processEvents()  # <---先处理一次事件,获取响应的rect,不然输入事件会不同步
        rect = self.__document.cursor().rect()
        if rect.top() < self.verticalScrollBar().value():
            self.verticalScrollBar().setValue(int(rect.top()))
        elif rect.bottom() > self.verticalScrollBar().value() + self.viewport().height():
            self.verticalScrollBar().setValue(int(rect.bottom() - self.viewport().height()))

    def document(self) -> MarkDownDocument:
        return self.__document
