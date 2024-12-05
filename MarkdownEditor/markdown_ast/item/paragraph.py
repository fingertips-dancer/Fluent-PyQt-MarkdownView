import typing as t

from ..base import MarkdownASTBase
from ...style import MarkdownStyle
from ...abstruct import AbstructCursor
from ...abstruct import AbstructCachePaint, AbstructTextParagraph


@MarkdownASTBase.registerAst("paragraph")
class Paragraph(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]

    # html tag
    htmlTag = "p"

    def toMarkdown(self) -> str:
        return "".join([c.toMarkdown() for c in self.children]) + "\n"

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        font = style.hintFont(font=ht.painter().font(), ast="paragraph")
        ht.painter().setFont(font)
        for c in self.children:
            c.render(ht, style=style, cursor=cursor)
        ht.renderContent(func=AbstructTextParagraph.Render_HardBreak, ast=self)
        ht.newParagraph()

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        s = []
        for c in self.children:
            s += c.segment()
        return s
