import typing as t

from ..base import MarkdownASTBase
from ...style import MarkdownStyle
from ...abstruct import AbstructCursor
from ...abstruct import AbstructCachePaint


@MarkdownASTBase.registerAst("block_text")
class BlockText(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]

    htmlTag = ""

    def toMarkdown(self) -> str:
        return "".join([c.toMarkdown() for c in self.children])

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="block_text"))
        for c in self.children:
            c.render(ht, style=style, cursor=cursor)

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        s = []
        for c in self.children:
            s += c.segment()
        return s
