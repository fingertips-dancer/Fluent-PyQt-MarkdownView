import typing as t

from PyQt5.QtCore import QMargins, QRect
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor, QPixmap

# from .cursor import MarkdownCursor
from .abstruct import AbstructCachePaint
from .component import TextParagraph
from .markdown_ast import MarkdownASTBase


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
        super(CachePaint, self).__init__(parent)
        # 垂直距离
        # self._parent: AbstractMarkDownDocument = parent
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
        # cache ast geometry drawing
        self._cachePaintingGeometry: t.Dict[MarkdownASTBase, QRect] = {}

    def renderContent(self, func, ast: MarkdownASTBase, data=None):
        self._paragraphs[-1].pullRenderCache(func=func, data=data, painter=self.painter(), ast=ast)

    def render(self, resetCache=True) -> t.Dict[MarkdownASTBase, QPixmap]:
        """ 渲染 """

        def _finish_a_ast_render():
            if len(ast_part_pixmaps) > 0:  # merge mutil pixmap
                pixmap = QPixmap(ast_part_pixmaps[0].width(), sum(pm.height() for pm in ast_part_pixmaps))
                if pixmap.height() != 0:
                    pixmap.fill(QColor(0, 0, 0, 0))
                    painter, y = QPainter(pixmap), 0
                    for pm in ast_part_pixmaps:
                        painter.drawPixmap(0, y, pm)
                        y += pm.height()
                    pixmaps.append(pixmap)
                    painter.end()
                pbs, y = [], 0
                for mp, part_CursorPluginBases in zip(ast_part_pixmaps, ast_part_CursorPluginBases):
                    offest = QPointF(0, y)
                    pbs += [(ast, b + offest) for ast, b in part_CursorPluginBases]
                    y += mp.height()

            if len(ast_part_pixmaps) != 0:
                self._cachePxiamp[now_ast] = pixmap  # a pixmap for a ast
                self._cacheCursorPluginBases[now_ast] = pbs
                self._cacheTextParagraphs[now_ast] = ast_part_TextParagraphs

        pixmaps = []
        ast_part_pixmaps = []
        ast_part_CursorPluginBases = []
        ast_part_TextParagraphs = []
        now_ast = None
        if resetCache:
            self._cachePxiamp.clear()
            self._cacheCursorPluginBases.clear()
            self._cacheTextParagraphs.clear()
            self._cachePaintingGeometry.clear()

        the_len = len(self._paragraphs)

        for idx, p in enumerate(self._paragraphs):
            p.setInPragraphReutrnSpace(self._inPragraphReutrnSpace)
            p.setOutPragraphReutrnSpace(self._outPragraphReutrnSpace)
            p.setPageMargins(self._margins)
            p.setViewWdith(self._viewWdith)
            # render
            pximap_part = p.render()
            if p.ast() is not now_ast:  # <-- The ast now painteed transform
                _finish_a_ast_render()

                ast_part_pixmaps = []  # reset
                ast_part_CursorPluginBases = []
                ast_part_TextParagraphs = []

            # register
            ast_part_pixmaps.append(pximap_part)
            ast_part_CursorPluginBases.append(p.cursorBases())
            ast_part_TextParagraphs.append(p)

            # update
            now_ast = p.ast()
        _finish_a_ast_render()
        return

    def reset(self):
        self._paragraphs = []

    def newSubParagraph(self):
        """" 新的的子段落, 使用上下文来让子控件添加数据 """
        tp = TextParagraph()

        class proxy():
            def __enter__(cls):
                # 临时添加
                self._paragraphs.append(tp)
                return tp

            def __exit__(cls, exc_type, exc_val, exc_tb):
                self._paragraphs.pop(-1)
                if exc_type is not None:
                    print(exc_type)
                    raise exc_type
                return False

        return proxy()

    def newParagraph(self):
        """新的根段落 """
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

    def painter(self) -> QPainter:
        return self._painter

    def textParagraphs(self, ast=None, pos: int = None) -> t.List[TextParagraph] or TextParagraph:
        if ast is None:
            return self._paragraphs
        elif pos is None:
            return self._cacheTextParagraphs[ast]
        else:
            ps = self.textParagraphs(ast=ast)
            for p in ps:
                if pos > len(p.cursorBases()):
                    pos -= len(p.cursorBases())
                    continue
                return p

    def cachePxiamp(self, ast=None) -> t.Dict[MarkdownASTBase, QPixmap] or QPixmap:
        if ast:
            return self._cachePxiamp[ast]
        return self._cachePxiamp

    def height(self) -> int:
        return sum(pm.height() for pm in self._cachePxiamp.values())

    def cursorPluginBases(self, ast,
                          pos: t.Optional[int] = None,
                          returnAst: bool = False) -> t.Union[QPointF, t.List[QPointF]]:
        cps = self._cacheCursorPluginBases[ast] if returnAst else [p for ast, p in self._cacheCursorPluginBases[ast]]
        return cps[pos] if pos is not None else cps

    def lineHeight(self, ast, pos: int) -> int:
        p: TextParagraph = self.textParagraphs(ast=ast, pos=pos)
        if p:
            return p.lineHeight()
        raise Exception(ast, sum(len(p.cursorBases()) for p in self.textParagraphs(ast)), "but", pos)

    def indentation(self, ast, pos: int) -> int:
        p: TextParagraph = self.textParagraphs(ast=ast, pos=pos)
        if p:
            return p.indentation()
        raise Exception(ast, sum(len(p.cursorBases()) for p in self.textParagraphs(ast)), "but", pos)

    def paintGeometry(self, ast) -> QRect:
        pass
