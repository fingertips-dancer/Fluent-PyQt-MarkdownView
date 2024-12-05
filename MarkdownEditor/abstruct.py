import typing as t

from PyQt5.QtCore import QPointF, QTimer, QRectF, QObject, QMargins, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QFont, QBrush, QColor, QTextDocument


class AbstractMarkDownDocument(QTextDocument):
    textChanged = pyqtSignal()
    Header1 = 36

    fontType = 'Arial'
    headerSize = [36, 34, 32, 30, 28, 26]
    pragraphSize = 20

    # 换行间隔
    inPragraphReutrnSpace = 5
    # 段落换行
    outPragraphReutrnSpace = 10

    # signal
    heightChanged = pyqtSignal(int)

    def __init__(self):
        super(AbstractMarkDownDocument, self).__init__()
        self._text: str = ""
        self._painter: QPainter = None
        self._margings = QMargins(15, 15, 15, 15)  # 边缘
        self._viewWidth = 100  # 文本宽度
        self._height = 10  # 文本长读

    def setPainter(self, p: QPainter):
        self._painter = p

    def painter(self) -> QPainter:
        return self._painter

    def margings(self) -> QMargins:
        return self._margings

    def resetInViewItem(self):
        self._inViewItem = []

    def textParagraphs(self) -> t.List['AbstructTextParagraph']:
        raise ImportError


class AbstructCursor(QObject):
    SELECT_MODE_SINGLE = 1
    SELECT_MODE_MUTIL = 2

    MOVE_FELT = "left"
    MOVE_RIGHT = "right"
    MOVE_MOUSE = "mouse"
    MOVE_DOWN = "down"
    MOVE_UP = "up"

    POSITION_END = "end"
    POSITION_START = "start"

    def __init__(self, parent):
        super(AbstructCursor, self).__init__(parent)

        self._ast = None
        self._pos = -1
        self._rect = QRectF(1, 1, 1, 1)
        self._selectStart: t.Tuple['MarkdownASTBase', int] = None  # 全选
        self._select_mode = self.SELECT_MODE_SINGLE  # 单选模式
        # 光标闪烁标志位
        # 光标闪烁标志位翻转
        self.__showCursorShader = True
        self.showCursorShaderTimer = QTimer()
        self.showCursorShaderTimer.timeout.connect(
            lambda: (self.setIsShowCursorShader(not self.__showCursorShader)))
        self.showCursorShaderTimer.setSingleShot(False)
        self.showCursorShaderTimer.start(700)

    def setIsShowCursorShader(self, _is: bool):
        self.__showCursorShader = _is
        self.showCursorShaderTimer.stop()
        self.showCursorShaderTimer.start(700)

    def isShowCursorShader(self) -> bool:
        return self.__showCursorShader

    def add(self, text: str) -> None:
        """添加文本"""
        raise NotImplementedError

    def pop(self, _len):
        # 1.删除长度太长
        # 1.1剔除一个父类
        raise NotImplementedError

    def _return(self):
        """换行"""
        raise NotImplementedError

    def move(self, flag, pos: QPointF = None):
        raise NotImplementedError

    def render(self):
        raise NotImplementedError

    def pos(self) -> int:
        return self._pos

    def rect(self) -> QRectF:
        raise NotImplementedError

    def setPos(self, pos: int):
        """ 设置索引 """
        assert isinstance(pos, (int, str)), ""
        if isinstance(pos, int):
            pos = pos
        else:
            assert pos in (self.POSITION_END, self.POSITION_START), ""
            if pos == self.POSITION_END:
                pos = len(self.ast().toMarkdown()) - 1
            elif pos == self.POSITION_START:
                pos = 0

        # 当前容纳不下
        if pos >= 0:  # 向前
            for ast in self.rootAst().children[self.rootAst().index(self.ast()):]:
                t = len(ast.toMarkdown())
                if pos >= t:
                    pos -= t
                else:
                    self._ast, self._pos = ast, pos
                    break
            else:
                self._ast, self._pos = self.rootAst().astOf(-1), len(ast.toMarkdown()) - 1  # 末端
        else:  # 向后
            for ast in self.rootAst().children[:self.rootAst().index(self.ast())][::-1]:
                pos += len(ast.toMarkdown())
                if pos >= 0:
                    self._ast, self._pos = ast, pos
                    break
            else:
                self._ast, self._pos = self.rootAst().astOf(0), 0  # 顶端

    def setAST(self, ast, pos=None):
        """ set position """
        assert ast is not None, ""
        self._ast = ast
        if pos: self.setPos(pos)

    def isIn(self, ast) -> bool:
        """" 是否在其中"""
        raise NotImplementedError

    def setSelectMode(self, mode):
        """ 设置选择模式 """
        self._select_mode = mode
        if mode == self.SELECT_MODE_MUTIL:
            self._selectStart = (self.ast(), self.pos())
        else:
            self._selectStart = (self.ast(), self.pos())

    def selectedASTs(self) -> t.Tuple['MarkdownASTBase', int, 'MarkdownASTBase', int]:
        """ 被选中的ast """
        if self.selectMode() == self.SELECT_MODE_SINGLE:
            return self.ast(), self.pos(), self.ast(), self.pos()
        idx1, idx2 = self.rootAst().index(self.ast()), self.rootAst().index(self._selectStart[0])
        if idx1 < idx2:
            return self.ast(), self.pos(), self._selectStart[0], self._selectStart[1]
        elif idx1 > idx2:
            return self._selectStart[0], self._selectStart[1], self.ast(), self.pos()
        else:
            if self.pos() > self._selectStart[1]:
                return self.ast(), self._selectStart[1], self.ast(), self.pos()
            else:
                return self.ast(), self.pos(), self.ast(), self._selectStart[1]

    def selectMode(self):
        return self._select_mode

    def rootAst(self) -> 'MarkdownAstRoot':
        """ root ast """
        return self.ast().parent

    def ast(self) -> 'MarkdownASTBase':
        return self._ast


class AbstructTextParagraph():
    """ 一个绘制段落 """
    Render_Image = 1
    Render_Text = 2
    Render_HideText = 3
    Render_BlockLatexText = 4
    Render_BlockLatexImage = 5
    Render_InlineLatexImage = 6
    Render_SoftBreak = 7
    Render_HardBreak = 8
    Render_BlankLine = 9
    Render_SerialNumber = 10
    Render_InlineLatexText = 11

    def __init__(self):
        self._cache: t.List[t.Tuple[t.Callable, t.Any, 'MarkdownASTBase', QFont, QBrush, QPen]] = []
        self.__viewWdith = 512
        self.__pageMargins: QMargins = QMargins()
        self.__outPragraphReutrnSpace = 15
        self.__inPragraphReutrnSpace = 10
        self.__lineHight: int = None  # 一行的高度
        self.__painter_pos = QPointF()  # 绘制坐标
        self.__paragraph_ast: 'MarkdownASTBase' = None  # 段落的根节点
        self.__cursor_bases: t.List[QPointF] = []  # 光标的位置

        # only
        self.__indentation = 0  # 缩进
        self.__backgroundRaidus = 0  # 圆角半径
        self.__backgroundColor = QColor(0, 0, 0, 0)  # 背景颜色
        self.__backgroundEnable = False  # 使能
        self.__backgroundMargins = QMargins(0, 0, 0, 0)

    def clearAllcursorBases(self) -> None:
        """ clear all cursor base"""
        self.__cursor_bases.clear()

    def addCursorBase(self, pos):
        """ add a cursor base"""
        self.__cursor_bases.append(pos)

    def setPaintPoint(self, pos):
        """ 绘制点 """
        self.__painter_pos = pos

    def setLineHeight(self, height: int or float):
        """ 段落的高 """
        self.__lineHight = height

    def setAST(self, ast: 'MarkdownASTBase'):
        """ ast """
        self.__paragraph_ast = ast

    def setStartY(self, y: float or int):
        """ 绘制坐标"""
        self.__painter_pos = QPointF(self.margins().left() + self.__indentation, y)

    def setViewWdith(self, width: float):
        """ 窗口宽度 """
        self.__viewWdith = width

    def setPageMargins(self, margins: QMargins):
        """ 绘制边距 """
        self.__pageMargins = margins

    def setIndentation(self, indentation):
        """ 缩进 """
        self.__indentation = indentation

    def setBackgroundColor(self, color: QColor):
        """ 设置背景颜色 """
        self.__backgroundColor = color

    def setBackgroundRadius(self, radius: float):
        """ 设置背景颜色 """
        self.__backgroundRadius = radius

    def setOutPragraphReutrnSpace(self, space: int):
        """ 段落外缩进"""
        self.__outPragraphReutrnSpace = space

    def setInPragraphReutrnSpace(self, space: int):
        """ 段落内缩进 """
        self.__inPragraphReutrnSpace = space

    def setBackgroundEnable(self, enable: bool):
        """ 设置背景使能 """
        self.__backgroundEnable = enable

    def setBackgroundMargins(self, left, up, right, bottom):
        """ 设置背景使能 """
        self.__backgroundMargins = QMargins(left, up, right, bottom)

    """ property """

    def margins(self) -> QMargins:
        """ 绘制边距 """
        return self.__pageMargins + self.__backgroundMargins

    def pageMargins(self) -> QMargins:
        """ 绘制边距 """
        return self.__pageMargins
    def length(self) -> int:
        """ property: 渲染项 """
        return len(self._cache)

    def lineHeight(self) -> float:
        """ 段落的高 """
        return self.__lineHight

    def indentation(self):
        """ 缩进 """
        return self.__indentation

    def ast(self) -> 'MarkdownASTBase':
        """ ast """
        return self.__paragraph_ast

    def cursorBaseof(self, idx) -> QPointF:
        """ 位于 idx 的 cursor 位置 """
        return self.__cursor_bases[idx]

    def cursorBases(self) -> t.List[QPointF]:
        """ 所有 cursor 位置 """
        return self.__cursor_bases

    def backgroundColor(self):
        """ 设置背景颜色 """
        return self.__backgroundColor

    def backgroundRaidus(self):
        """ 设置背景颜色 """
        return self.__backgroundRadius

    def paintPoint(self) -> QPointF:
        """ 绘制点 """
        return self.__painter_pos

    def viewWdith(self):
        """ 窗口宽度 """
        return self.__viewWdith

    def inPragraphReutrnSpace(self, ):
        """ 段落内缩进 """
        return self.__inPragraphReutrnSpace

    def outPragraphReutrnSpace(self, ):
        """ 段落外缩进 """
        return self.__outPragraphReutrnSpace

    def backgroundEnable(self):
        """ 背景使能 """
        return self.__backgroundEnable

    def backgroundMargins(self) -> QMargins:
        return self.__backgroundMargins


class AbstructCachePaint():
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
        self._paragraphs: t.List[AbstructTextParagraph] = []

    def newParagraph(self):
        """ 创建一个新的 Paragraph """
        raise NotImplementedError

    def renderContent(self, func, ast, data=None):
        """ paint """
        raise NotImplementedError

    def renderCursor(self, cursor: AbstructCursor):
        raise NotImplementedError

    def setPainter(self, painter: QPainter):
        raise NotImplementedError

    def setStartPos(self, pos: QPainter):
        raise NotImplementedError

    def setPaperWidth(self, width):
        raise NotImplementedError

    def setMargins(self, margins):
        raise NotImplementedError

    def painter(self) -> QPainter:
        """ QPainter """
        raise NotImplementedError

    def nowParagraph(self) -> AbstructTextParagraph:
        """ 当前的 Paragraph """
        return self._paragraphs[-1]
