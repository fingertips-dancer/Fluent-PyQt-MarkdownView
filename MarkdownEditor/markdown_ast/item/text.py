import typing as t

from ..base import MarkdownASTBase
from ...component import MarkdownStyle
from ...abstruct import AbstructCursor
from ...abstruct import AbstructHorizontalText, AbstructTextParagraph


@MarkdownASTBase.registerAst("text")
class Text(MarkdownASTBase):
    type: str
    raw: str
    propertys = ["type", "raw"]

    # html tag
    htmlTag = ""

    def toMarkdown(self) -> str:
        return self.raw

    def render(self, ht: AbstructHorizontalText, style: MarkdownStyle, cursor: AbstructCursor = None):
        ht.renderContent(func=AbstructTextParagraph.Render_Text, data=self.raw, ast=self)

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        return [(self, len(self.raw))]


@MarkdownASTBase.registerAst("strong")
class Strong(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]

    # html tag
    htmlTag = "strong"

    def toMarkdown(self) -> str:
        return "**" + "".join([c.toMarkdown() for c in self.children]) + "**"

    def render(self, ht: AbstructHorizontalText, style: MarkdownStyle, cursor: AbstructCursor = None):
        oriF = ht.painter().font()
        ht.painter().setFont(style.hintFont(ht.painter().font(), ast="strong"))

        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        if isShowHide:
            ht.renderContent(func=AbstructTextParagraph.Render_Text, data="**", ast=self)
            for c in self.children: c.render(ht, style=style, cursor=cursor)
            ht.renderContent(func=AbstructTextParagraph.Render_Text, data="**", ast=self)
        else:
            ht.renderContent(func=AbstructTextParagraph.Render_HideText, data="**", ast=self)
            for c in self.children: c.render(ht, style=style, cursor=cursor)
            ht.renderContent(func=AbstructTextParagraph.Render_HideText, data="**", ast=self)
        ht.painter().setFont(oriF)

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        s = []
        for c in self.children:
            s += c.segment()
        return [(self, 1)] + s + [(self, 1)]


@MarkdownASTBase.registerAst("emphasis")
class Emphasis(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]

    htmlTag = "em"

    def toMarkdown(self) -> str:
        return "*" + "".join([c.toMarkdown() for c in self.children]) + "*"

    def render(self, ht: AbstructHorizontalText, style: MarkdownStyle, cursor: AbstructCursor = None):
        oriF = ht.painter().font()
        ht.painter().setFont(style.hintFont(ht.painter().font(), ast="emphasis"))

        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        if isShowHide:
            ht.renderContent(func=AbstructTextParagraph.Render_Text, data="*", ast=self)
            for c in self.children: c.render(ht, style=style, cursor=cursor)
            ht.renderContent(func=AbstructTextParagraph.Render_Text, data="*", ast=self)
        else:
            ht.renderContent(func=AbstructTextParagraph.Render_HideText, data="*", ast=self)
            for c in self.children: c.render(ht, style=style, cursor=None)
            ht.renderContent(func=AbstructTextParagraph.Render_HideText, data="*", ast=self)
        ht.painter().setFont(oriF)

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        s = []
        for c in self.children:
            s += c.segment()
        return [(self, 2)] + s + [(self, 2)]
