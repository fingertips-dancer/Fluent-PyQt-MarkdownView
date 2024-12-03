from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPen, QColor

_global = "global"
default = 'default'
font = 'font'
pen = 'pen'
brush = 'brush'
pointsize = "pointsize"


class MarkdownStyle():
    defaultStyle = {
        default: {pointsize: 20, brush: Qt.NoBrush, pen: Qt.NoPen},
        "header": {}
    }
    fontType = 'Arial'
    headerSize = [36, 34, 32, 30, 28, 26]
    pragraphSize = 20

    def __init__(self):
        pass

    def inPragraphReutrnSpace(self):
        # 换行间隔
        return 5

    def outPragraphReutrnSpace(self):
        # 段落换行
        return 10

    def hintFont(self, font: QFont, ast: str, **kwargs):
        if ast == "header":
            font.setPointSize([36, 34, 32, 30, 28, 26][kwargs["level"] - 1])
            font.setBold(False)
        elif ast == "paragraph":
            font.setPointSize(20)
            font.setBold(False)
        elif ast == "strong":
            font.setBold(True)
        elif ast == "emphasis":
            font.setItalic(True)
        elif ast == "list":
            font.setPointSize(20)
        elif ast == "list_item":
            font.setPointSize(20)
        elif ast == "block_math":
            font.setPointSize(20)
        elif ast == "blank_line":
            font.setPointSize(20)
            font.setBold(False)
            font.setItalic(False)
        return font

    def hintPen(self, pen: QPen, ast: str, **kwargs):
        if ast == "header":
            if kwargs["hide"]:
                pen.setColor(Qt.gray)
            else:
                pen.setColor(Qt.black)
        elif ast == "image":
            pen.setColor(Qt.gray)
        else:
            pen.setColor(Qt.black)
        # elif ast == "paragraph":
        #     pen.setPointSize(20)
        # elif ast == "list":
        #     pen.setPointSize(20)
        # elif ast == "list_item":
        #     pen.setPointSize(20)
        return pen

    def hintIndentation(self, ast: str, **kwargs) -> int:
        """ 推荐缩进 """
        if ast == "block_math":
            indentation = 15
        else:
            indentation = 0
        return indentation

    def hintBackgroundColor(self, ast: str) -> QColor:
        """ 背景颜色 """
        c = QColor(0, 0, 0, 0)
        if ast == "block_math":
            c = QColor(16, 16, 16, 16)

        return c

    def hintBackgroundRadius(self, ast: str) -> float:
        """ 背景圆角半径 """
        c = 15
        return c
