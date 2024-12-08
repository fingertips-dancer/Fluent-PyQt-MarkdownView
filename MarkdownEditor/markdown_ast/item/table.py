import typing as t

from ..base import MarkdownASTBase
from ...abstruct import AbstructCachePaint
from ...abstruct import AbstructCursor
from ...abstruct import AbstructTextParagraph as ATP
from ...style import MarkdownStyle


@MarkdownASTBase.registerAst("table")
class Table(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]

    def toMarkdown(self) -> str:
        raw = ''.join(c.toMarkdown() for c in self.children)
        if raw == self.url:# <url>
            return rf'<' + f'{self.url}' + '>'
        else:
            return rf'[{raw}]({self.url})'


    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)

        if isShowHide:
            ht.painter().save()
            ht.painter().setFont(style.hintFont(font=ht.painter().font(),ast="link",pseudo="hidden"))
            ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="link", pseudo="hidden"))
            ht.renderContent(func=ATP.Render_Text, data=self.toMarkdown(), ast=self)
            ht.painter().restore()
        else:  # <url>
            ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="link"))
            ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="link"))
            ht.renderContent(func=ATP.Render_HideText, data='<', ast=self)
            ht.renderContent(func=ATP.Render_Text, data=''.join(c.toMarkdown() for c in self.children), ast=self)
            ht.renderContent(func=ATP.Render_HideText, data='>', ast=self)

        # ht.text(text=self.toMarkdown(), ast=self)
@MarkdownASTBase.registerAst("table_head")
class TableHead(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]
    attrs = []

    def toMarkdown(self) -> str:
        raw = ''.join(c.toMarkdown() for c in self.children)
        if raw == self.url:# <url>
            return rf'<' + f'{self.url}' + '>'
        else:
            return rf'[{raw}]({self.url})'


    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)

        if isShowHide:
            ht.painter().save()
            ht.painter().setFont(style.hintFont(font=ht.painter().font(),ast="link",pseudo="hidden"))
            ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="link", pseudo="hidden"))
            ht.renderContent(func=ATP.Render_Text, data=self.toMarkdown(), ast=self)
            ht.painter().restore()
        else:  # <url>
            ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="link"))
            ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="link"))
            ht.renderContent(func=ATP.Render_HideText, data='<', ast=self)
            ht.renderContent(func=ATP.Render_Text, data=''.join(c.toMarkdown() for c in self.children), ast=self)
            ht.renderContent(func=ATP.Render_HideText, data='>', ast=self)

        # ht.text(text=self.toMarkdown(), ast=self)
@MarkdownASTBase.registerAst("table_body")
class TableBody(MarkdownASTBase):
    type: str
    align:str
    head:bool
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]

    def toMarkdown(self) -> str:
        raw = ''.join(c.toMarkdown() for c in self.children)
        if raw == self.url:# <url>
            return rf'<' + f'{self.url}' + '>'
        else:
            return rf'[{raw}]({self.url})'


    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)

        if isShowHide:
            ht.painter().save()
            ht.painter().setFont(style.hintFont(font=ht.painter().font(),ast="link",pseudo="hidden"))
            ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="link", pseudo="hidden"))
            ht.renderContent(func=ATP.Render_Text, data=self.toMarkdown(), ast=self)
            ht.painter().restore()
        else:  # <url>
            ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="link"))
            ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="link"))
            ht.renderContent(func=ATP.Render_HideText, data='<', ast=self)
            ht.renderContent(func=ATP.Render_Text, data=''.join(c.toMarkdown() for c in self.children), ast=self)
            ht.renderContent(func=ATP.Render_HideText, data='>', ast=self)

@MarkdownASTBase.registerAst("table_cell")
class TableCell(MarkdownASTBase):
    type: str
    align: str
    head: bool
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]
    attrs = ["align", "head"]

    def toMarkdown(self) -> str:
        raw = ''.join(c.toMarkdown() for c in self.children)
        if raw == self.url:  # <url>
            return rf'<' + f'{self.url}' + '>'
        else:
            return rf'[{raw}]({self.url})'

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)

        if isShowHide:
            ht.painter().save()
            ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="link", pseudo="hidden"))
            ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="link", pseudo="hidden"))
            ht.renderContent(func=ATP.Render_Text, data=self.toMarkdown(), ast=self)
            ht.painter().restore()
        else:  # <url>
            ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="link"))
            ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="link"))
            ht.renderContent(func=ATP.Render_HideText, data='<', ast=self)
            ht.renderContent(func=ATP.Render_Text, data=''.join(c.toMarkdown() for c in self.children), ast=self)
            ht.renderContent(func=ATP.Render_HideText, data='>', ast=self)

@MarkdownASTBase.registerAst("table_row")
class TableRow(MarkdownASTBase):
    type: str
    align: str
    head: bool
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]

    def toMarkdown(self) -> str:
        raw = ''.join(c.toMarkdown() for c in self.children)
        if raw == self.url:  # <url>
            return rf'<' + f'{self.url}' + '>'
        else:
            return rf'[{raw}]({self.url})'

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)

        if isShowHide:
            ht.painter().save()
            ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="link", pseudo="hidden"))
            ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="link", pseudo="hidden"))
            ht.renderContent(func=ATP.Render_Text, data=self.toMarkdown(), ast=self)
            ht.painter().restore()
        else:  # <url>
            ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="link"))
            ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="link"))
            ht.renderContent(func=ATP.Render_HideText, data='<', ast=self)
            ht.renderContent(func=ATP.Render_Text, data=''.join(c.toMarkdown() for c in self.children), ast=self)
            ht.renderContent(func=ATP.Render_HideText, data='>', ast=self)