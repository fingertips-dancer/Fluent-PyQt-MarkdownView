import typing as t

from PyQt5.QtCore import QMargins, Qt, QRectF, QSizeF
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QImage, QColor
from superfluentwidget.Backend import ThemeColor

# from .cursor import MarkdownCursor
from .abstruct import AbstractMarkDownDocument
from .abstruct import AbstructCursor
from .abstruct import AbstructHorizontalText
from .markdown_ast import MarkdownASTBase
from .text_paragraph import TextParagraph


def paintMemory(func):
    def wapper(*args, **kwargs):
        cls: HorizontalText = args[0]
        font, pen = cls._painter.font(), cls._painter.pen()
        r = func(*args, **kwargs)
        cls._painter.setPen(pen)
        cls._painter.setFont(font)
        return r

    return wapper


class HorizontalText(AbstructHorizontalText):
    def __init__(self, parent):

        # 垂直距离
        self._parent: AbstractMarkDownDocument = parent
        self._verticalSpace: int = 10
        self._painter: QPainter = None
        self._painter_pos: QMargins = None
        self._margins: QMargins = None
        self._leftEdge: float = None
        self._viewWdith: float = None
        # self._cursor: MarkdownCursor = None
        self.__mutilMedia = {}
        self._inPragraphReutrnSpace = 5
        self._outPragraphReutrnSpace = 5
        # 显示范围,text item,对应的文本
        self._paragraphs: t.List[TextParagraph] = []

    def setNowParagraphBackgroundColor(self, color: QColor):
        """ 设置当前段落背景颜色 """
        self._paragraphs[-1].setBackgroundColor(color=color)

    def setNowParagraphBackgroundRadius(self, radius: float or int):
        """ 设置当前段落背景半径 """
        self._paragraphs[-1].setBackgroundRadius(radius=radius)

    def setNowParagraphIndentation(self, indentation):
        self._paragraphs[-1].setIndentation(indentation=indentation)

    def renderContent(self, func, ast: MarkdownASTBase, data=None):
        self._paragraphs[-1].pullRenderCache(func=func, data=data, painter=self.painter(), ast=ast)



    @paintMemory
    def image(self, image: str, ast=None):
        if image not in self.__mutilMedia:
            self.__mutilMedia[image] = QImage(image)
        image: QImage = self.__mutilMedia[image]
        self._paragraphs[-1].pullRenderCache(func=TextParagraph.Render_Image,
                                             data=image, painter=self.painter(), ast=ast)

    def render(self):
        """ 渲染 """
        y = self._painter_pos.y()
        for p in self._paragraphs:
            p.setInPragraphReutrnSpace(self._inPragraphReutrnSpace)
            p.setOutPragraphReutrnSpace(self._outPragraphReutrnSpace)
            p.setMargins(self._margins)
            p.setViewWdith(self._viewWdith)
            p.setStartY(y)
            y = p.render(self.painter())
        return y

    @paintMemory
    def renderCursor(self, cursor: AbstructCursor, radius=5):
        # item, s = self.inViewItemWith(ast=cursor.ast(), pos=cursor.pos())
        # 寻找包含这个节点的段落
        if cursor.isShowCursorShader():
            ps = [p for p in self._paragraphs if cursor.ast() is p.ast()]
            # 绘制
            base_length = cursor.pos()
            for p in ps:
                if p.ast() is not cursor.ast():
                    continue

                if len(p.cursorBases()) <= base_length:
                    base_length -= len(p.cursorBases())
                    continue
                else:
                    try:
                        pos = p.cursorBaseof(idx=base_length)
                        self.painter().drawLine(pos, pos + QPointF(0, p.lineHeight()))
                        break
                    except Exception as e:
                        print("error", len(p.cursorBases()), base_length)
                        raise e
            else:
                raise Exception("没找到",
                                cursor.ast(),
                                cursor.ast().toMarkdown(),
                                len(cursor.ast().toMarkdown()),
                                cursor.pos())

        if cursor.selectMode() != cursor.SELECT_MODE_MUTIL: return

        # 2.绘制多选
        start_ast, start_pos, end_ast, end_pos = cursor.selectedASTs()
        if start_ast is start_ast and start_pos == end_pos: return  # 原地
        isStartShow = False
        # 2.0.5渲染
        color = ThemeColor.PRIMARY.color()
        color.setAlpha(125)
        self.painter().setPen(Qt.NoPen)
        self.painter().setBrush(color)
        for p in self.textParagraphs():
            # 2.1 判断是否开始渲染
            # 2.1.1 开始渲染了是否还没开始或结束
            if isStartShow or p.ast() is start_ast:
                isStartShow = True
            if isStartShow and p.ast() is end_ast:
                isStartShow = False
            if not isStartShow and p.ast() is not end_ast:
                continue

            # 2.2 ast 的 cursor base
            # 2.3 删除起始和结束的多余项
            bs = p.cursorBases()
            _len_bs = len(bs)
            if p.ast() is start_ast:
                if _len_bs >= start_pos > 0:
                    bs = bs[start_pos:]
                    start_pos -= _len_bs
                start_pos -= _len_bs

            if p.ast() is end_ast:
                if _len_bs > end_pos > 0:  # 在同一段落,但还没开始
                    bs = bs[:len(bs) - (_len_bs - end_pos - 1)]
                end_pos -= _len_bs

            if start_pos > 0: continue
            if len(bs) < 2: continue
            # print(bs)
            left_top = bs[0]
            for b, next_b in zip(bs[:-1], bs[1:]):
                if next_b.y() > left_top.y():
                    self.painter().drawRoundedRect(QRectF(left_top,
                                                          QSizeF(b.x() - left_top.x(), p.lineHeight())),
                                                   radius, radius)
                    left_top = QPointF(p.margins().left() + p.indentation(), next_b.y())  # 下一行,update
            else:
                self.painter().drawRoundedRect(
                    QRectF(left_top, QSizeF(next_b.x() - left_top.x(), p.lineHeight())),
                    radius, radius)
            if end_pos <= 0:
                break

    def reset(self):
        self._paragraphs = []

    def newParagraph(self):
        """新的段落 """
        self._paragraphs.append(TextParagraph())

    def nowParagraph(self) -> TextParagraph:
        """现在的段落 """
        return self._paragraphs[-1]

    def setPainter(self, painter: QPainter):
        self._painter = painter

    def setStartPos(self, pos: QPainter):
        self._painter_pos = pos

    def setPaperWidth(self, width):
        self._viewWdith = width

    def setMargins(self, margins):
        self._margins = margins

    def setLeftEdge(self, edge):
        self._leftEdge = edge
        # 传递给

    def leftEdge(self) -> float:
        return self._leftEdge

    def startPos(self) -> QPointF:
        return self._painter_pos

    def painter(self) -> QPainter:
        return self._painter

    def textParagraphs(self) -> t.List[TextParagraph]:
        return self._paragraphs
