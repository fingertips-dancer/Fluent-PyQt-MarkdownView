from PyQt5.QtGui import QFont

from .abstruct import AbstractMarkDownDocument
from .component import MarkdownStyle
from .cursor import MarkdownCursor
from .horizontal_text import HorizontalText
from .markdown_ast import MarkdownAstRoot
from .render_function import *


class MarkDownDocument(AbstractMarkDownDocument):
    def __init__(self):
        super(MarkDownDocument, self).__init__()
        self._cursor = MarkdownCursor(self)
        self._horizontalText = HorizontalText(self)
        self.__mutilMedia = {}  # 多媒体
        self.markdownAst: MarkdownAstRoot

    def render(self, painter: QPainter, rect: QRectF) -> None:
        """ 渲染 """
        # 模拟字体-段落
        font = QFont()
        font.setFamily(self.fontType)
        font.setBold(False)
        font.setItalic(False)
        font.setPointSize(self.pragraphSize)
        self.setPainter(painter)

        painter.translate(-rect.x(), -rect.y())
        # 设置绘制字体和颜色
        startPos, endPos = QPointF(self.margings().left(), self.margings().top()), QPointF(self.margings().left(),
                                                                                           self.margings().top())

        # 横线本
        self._horizontalText.setPainter(painter)
        self._horizontalText.setStartPos(startPos)
        self._horizontalText.setPaperWidth(self._viewWidth)
        self._horizontalText.setMargins(self.margings())
        self._horizontalText.setLeftEdge(self.margings().left())

        self._horizontalText.reset()
        self._horizontalText.newParagraph()  # 重置段落

        # 渲染登记
        self.__markdownAst.render(ht=self._horizontalText, style=MarkdownStyle(), cursor=self.cursor())
        # 正式渲染
        y = self._horizontalText.render()
        self._horizontalText.renderCursor(cursor=self.cursor())

        self.setPainter(None)
        self._horizontalText.setPainter(None)

        # 调整size
        height = y + 150
        if self.height() != height:
            self._height = height
            self.heightChanged.emit(self._height)
        painter.end()
        return

    def setMarkdown(self, markdown: str, **kwargs) -> None:
        self._text = markdown
        self.__markdownAst = MarkdownAstRoot()
        self.__markdownAst.setText(markdown)
        self.cursor().setAST(self.__markdownAst.children[0])
        self.cursor().setPos(0)
        print(self.__markdownAst.summary())

    def cursor(self) -> MarkdownCursor:
        return self._cursor

    def size(self) -> QSizeF:
        return QSizeF(self.viewportWidth(), self._height)

    def setViewportWidth(self, width: float) -> None:
        self._viewWidth = width

    def viewportWidth(self) -> int:
        return self._viewWidth

    def height(self):
        return self._height

    def textParagraphs(self) -> t.List[QPointF]:
        return self._horizontalText.textParagraphs()

    def toMarkdown(self) -> str:
        return self.markdownAst.toMarkdown()

    def ast(self) -> MarkdownAstRoot:
        return self.__markdownAst
