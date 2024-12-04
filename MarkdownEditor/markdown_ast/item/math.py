import typing as t

from ..base import MarkdownASTBase
from ...component import MarkdownStyle
from ...abstruct import AbstructCursor
from ...abstruct import AbstructCachePaint
from ...abstruct import AbstructTextParagraph as ATP


@MarkdownASTBase.registerAst("block_math")
class BlockMath(MarkdownASTBase):
    type: str
    raw: str
    propertys = ["type", 'raw']

    def toMarkdown(self) -> str:
        return "$$\n" + self.raw + "\n$$\n"

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        ph = ht.nowParagraph()
        ht.painter().setFont(style.hintFont(ht.painter().font(), ast="block_math"))
        if isShowHide:
            # 2. 添加缩进
            ph.setBackgroundEnable(True)
            ph.setBackgroundMargins(*style.hintBackgroundMargins(ast="block_math"))
            ph.setIndentation(indentation=style.hintIndentation(ast="block_math"))
            ph.setBackgroundColor(color=style.hintBackgroundColor(ast="block_math"))
            ph.setBackgroundRadius(radius=style.hintBackgroundRadius(ast="block_math"))
            # $$\n
            # self.raw + \n
            # $$\n
            ht.renderContent(func=ATP.Render_BlockLatexText, data=self.raw, ast=self)  # &&\n + raw + \n&&\n
            ht.newParagraph()  # <--避免渲染到 Latex
            ht.renderContent(func=ATP.Render_BlockLatexImage, data=self.raw, ast=self)
        else:
            ht.renderContent(func=ATP.Render_HideText, data=self.toMarkdown(), ast=self)
            ht.renderContent(func=ATP.Render_BlockLatexImage, data=self.raw, ast=self)
        ht.newParagraph()

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        s = []
        for c in self.children:
            s += c.segment()
        return [(self, len(self.toMarkdown()))]


@MarkdownASTBase.registerAst("inline_math")
class InlineMath(MarkdownASTBase):
    type: str
    raw: str
    propertys = ["type", 'raw']

    def toMarkdown(self) -> str:
        return "$" + self.raw + "$"

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        if isShowHide:
            # $ + self.raw + $

            ht.renderContent(func=ATP.Render_InlineLatexText, data=self.raw, ast=self)  # &&\n + raw + \n&&\n
        else:
            ht.renderContent(func=ATP.Render_HideText, data=self.toMarkdown(), ast=self)
            ht.renderContent(func=ATP.Render_InlineLatexImage, data=self.raw, ast=self)

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        s = []
        for c in self.children:
            s += c.segment()
        return [(self, len(self.toMarkdown()))]
