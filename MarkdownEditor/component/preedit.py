from PyQt5.QtCore import QObject, QEvent
from PyQt5.QtGui import QInputMethodEvent


class PreEdit(QObject):
    def __init__(self, parent: QObject = None):
        super(PreEdit, self).__init__(parent=parent)
        self.__preeditText = ""
        self.__replacementLength = 0
        self.__replacementStart = 0
        self.__cursorPos = 0
        parent.installEventFilter(self)

    def eventFilter(self, obj: 'QObject', event: QEvent) -> bool:
        if event.type() == QEvent.InputMethod:
            """输入法输入"""

            # 获取当前的候选词
            event:QInputMethodEvent

            # if len(event.attributes()) >= QInputMethodEvent.Cursor + 1:
            #     print("Cursor",event.attributes()[QInputMethodEvent.Cursor].value)
            #     print("Cursor", event.attributes()[QInputMethodEvent.Cursor].type)
            #     print("Cursor", event.attributes()[QInputMethodEvent.Cursor].start)
            # print(event.attributes())
            self.__preeditText = event.preeditString()  # 获取未最终确定的输入内容
            self.__replacementLength = event.replacementLength()
            self.__replacementStart = event.replacementStart()
            for attribute in event.attributes():
                if attribute.type == QInputMethodEvent.Cursor:
                    self.__cursorPos = attribute.start


        return False

    def preeditText(self) -> str:
        return self.__preeditText

    def replacementLength(self) -> int:
        return self.__replacementLength

    def replacementStart(self) -> int:
        return self.__replacementStart
    def cursorPos(self) -> int:
        return self.__cursorPos if len(self.preeditText()) else 0
