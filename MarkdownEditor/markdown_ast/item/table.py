import typing as t

from ..base import MarkdownASTBase
from ...abstruct import AbstructCachePaint, BlockLayer
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
        if raw == self.url:  # <url>
            return rf'<' + f'{self.url}' + '>'
        else:
            return rf'[{raw}]({self.url})'

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="paragraph"))
        ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="paragraph"))
        layer = BlockLayer(orientation=BlockLayer.Vertical)
        for c in self.children:
            with ht.newSubParagraph() as sub_ph:
                layer.addItem(sub_ph)
                c.render(ht, style=style, cursor=cursor)
        ht.renderContent(func=ATP.Render_ParagraphLayer, data=layer, ast=self)
        ht.nowParagraph().render()


@MarkdownASTBase.registerAst("table_head")
class TableHead(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]
    attrs = []

    def toMarkdown(self) -> str:
        raw = ' | '.join(c.toMarkdown() for c in self.children)
        if raw == self.url:  # <url>
            return rf'<' + f'{self.url}' + '>'
        else:
            return rf'[{raw}]({self.url})'

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="table th"))
        ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="table th"))
        hp = ht.nowParagraph()

        # background
        hp.setBackgroundEnable(True)
        hp.setBackgroundMargins(*style.hintBackgroundMargins(ast="table th"))
        hp.setBackgroundRadius(style.hintBorderRadius(ast="table th"))
        hp.setBackgroundColor(style.hintBackgroundColor(ast="table th"))

        layer = BlockLayer(orientation=BlockLayer.Horizontal)
        for c in self.children:
            with ht.newSubParagraph() as sub_ph:
                layer.addItem(sub_ph)
                c.render(ht=ht, style=style, cursor=cursor)
        ht.renderContent(func=ATP.Render_ParagraphLayer, data=layer, ast=self)

    # ht.text(text=self.toMarkdown(), ast=self)


@MarkdownASTBase.registerAst("table_body")
class TableBody(MarkdownASTBase):
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
        ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="paragraph"))
        ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="paragraph"))
        layer = BlockLayer(orientation=BlockLayer.Vertical)
        for idx, c in enumerate(self.children):
            with ht.newSubParagraph() as sub_ph:
                layer.addItem(sub_ph)
                sub_ph.setBackgroundEnable(True)
                sub_ph.setBackgroundMargins(*style.hintBackgroundMargins(ast="table tr", pseudo=f"nth-child({idx})"))
                sub_ph.setBackgroundRadius(style.hintBorderRadius(ast="table tr", pseudo=f"nth-child({idx})"))
                sub_ph.setBackgroundColor(style.hintBackgroundColor(ast="table tr", pseudo=f"nth-child({idx})"))
                c.render(ht=ht, style=style, cursor=cursor)
        ht.renderContent(func=ATP.Render_ParagraphLayer, data=layer, ast=self)


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
        ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="paragraph"))
        ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="paragraph"))

        layer = BlockLayer(orientation=BlockLayer.Horizontal)
        for c in self.children:
            with ht.newSubParagraph() as sub_ph:
                layer.addItem(sub_ph)
                c.render(ht=ht, style=style, cursor=cursor)
        ht.renderContent(func=ATP.Render_ParagraphLayer, data=layer, ast=self)


@MarkdownASTBase.registerAst("table_cell")
class TableCell(MarkdownASTBase):
    type: str
    align: str
    head: bool
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]
    attrs = ["align", "head"]

    def toMarkdown(self) -> str:
        return rf''.join(c.toMarkdown() for c in self.children)

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="paragraph"))
        ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="paragraph"))
        ph = ht.nowParagraph()
        ph.setAlign({"left": ph.AlignLeft, "right": ph.AlignRight, "center": ph.AlignCenter}[self.align])
        for c in self.children:
            c.render(ht=ht, style=style, cursor=cursor)
        ht.renderContent(func=ATP.Render_HardBreak, ast=self)
