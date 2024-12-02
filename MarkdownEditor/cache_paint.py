import typing as t

from PyQt5.QtCore import QMargins
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QImage, QColor, QPixmap

# from .cursor import MarkdownCursor
from .abstruct import AbstractMarkDownDocument
from .abstruct import AbstructCachePaint
from .markdown_ast import MarkdownASTBase
from .text_paragraph import TextParagraph


def paintMemory(func):
    def wapper(*args, **kwargs):
        cls: CachePaint = args[0]
        font, pen = cls._painter.font(), cls._painter.pen()
        r = func(*args, **kwargs)
        cls._painter.setPen(pen)
        cls._painter.setFont(font)
        return r

    return wapper


class CachePaint(AbstructCachePaint):
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
        # cachePixmap
        self._cachePxiamp: t.Dict[MarkdownASTBase, QPixmap] = {}
        # cursor plugin base
        self._cacheCursorPluginBases: t.Dict[MarkdownASTBase, t.List[QPointF]] = {}
        # cache TextParagraph
        self._cacheTextParagraphs: t.Dict[MarkdownASTBase, t.List[TextParagraph]] = {}

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

    def render(self, resetCache=True) -> t.Dict[MarkdownASTBase, QPixmap]:
        """ 渲染 """
        pixmaps = []
        ast_part_pixmaps = []
        ast_part_CursorPluginBases = []
        ast_part_TextParagraphs = []
        now_ast = None
        if resetCache:
            self._cachePxiamp.clear()
            self._cacheCursorPluginBases.clear()
            self._cacheTextParagraphs.clear()

        for p in self._paragraphs:
            p.setInPragraphReutrnSpace(self._inPragraphReutrnSpace)
            p.setOutPragraphReutrnSpace(self._outPragraphReutrnSpace)
            p.setMargins(self._margins)
            p.setViewWdith(self._viewWdith)
            # render
            pximap_part = p.render()
            if p.ast() is not now_ast:  # <-- The ast now painteed transform
                if len(ast_part_pixmaps) > 1:  # merge mutil pixmap
                    pixmap = QPixmap(ast_part_pixmaps[0].width(), sum(pm.height() for pm in ast_part_pixmaps))
                    pixmap.fill(QColor(0, 0, 0, 0))
                    painter = QPainter(pixmap)
                    y = 0
                    for pm in ast_part_pixmaps:
                        painter.drawPixmap(0, y, pm)
                        y += pm.height()
                    pixmaps.append(pixmap)
                    painter.end()
                    pbs, y = [], 0
                    for mp, part_CursorPluginBases in zip(ast_part_pixmaps, ast_part_CursorPluginBases):
                        offest = QPointF(0, y)
                        pbs += [b + offest for b in part_CursorPluginBases]
                        y += mp.height()

                elif len(ast_part_pixmaps) == 1:
                    pixmap = ast_part_pixmaps[0]
                    pbs = ast_part_CursorPluginBases[0]

                if len(ast_part_pixmaps) != 0:
                    self._cachePxiamp[now_ast] = pixmap  # a pixmap for a ast
                    self._cacheCursorPluginBases[now_ast] = pbs
                    self._cacheTextParagraphs[now_ast] = ast_part_TextParagraphs

                ast_part_pixmaps = []  # reset
                ast_part_CursorPluginBases = []
                ast_part_TextParagraphs = []
            # register
            ast_part_pixmaps.append(pximap_part)
            ast_part_CursorPluginBases.append(p.cursorBases())
            ast_part_TextParagraphs.append(p)
            # update
            now_ast = p.ast()
        return self._cachePxiamp

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

    def setPaperWidth(self, width):
        self._viewWdith = width

    def setMargins(self, margins):
        self._margins = margins

    def setLeftEdge(self, edge):
        self._leftEdge = edge
        # 传递给

    def leftEdge(self) -> float:
        return self._leftEdge

    def painter(self) -> QPainter:
        return self._painter

    def textParagraphs(self, ast=None) -> t.List[TextParagraph]:
        if ast is None:
            return self._paragraphs
        else:
            return self._cacheTextParagraphs[ast]

    def cachePxiamp(self) -> t.Dict[MarkdownASTBase, QPixmap]:
        return self._cachePxiamp

    def height(self) -> int:
        return sum(pm.height() for pm in self._cachePxiamp.values())

    def cursorPluginBases(self, ast, pos: t.Optional[int] = None) -> t.Union[QPointF, t.List[QPointF]]:
        if pos is not None:
            return self._cacheCursorPluginBases[ast][pos]
        else:
            return self._cacheCursorPluginBases[ast]

    def lineHeight(self, ast, pos: int) -> int:
        ps = self.textParagraphs(ast=ast)
        for p in ps:
            if pos > len(p.cursorBases()):
                pos -= len(p.cursorBases())
                continue
            return p.lineHeight()
        else:
            raise Exception(sum(len(p.cursorBases()) for p in self.textParagraphs(ast)),"but",pos)

    def indentation(self, ast, pos: int) -> int:
        ps = self.textParagraphs(ast=ast)
        for p in ps:
            if pos > len(p.cursorBases()):
                pos -= len(p.cursorBases())
                continue
            return p.indentation()
