import typing as t

from ..base import MarkdownASTBase
from ...component import MarkdownStyle
from ...abstruct import AbstructCursor
from ...abstruct import AbstructCachePaint


@MarkdownASTBase.registerAst("link")
class Link(MarkdownASTBase):
    type: str
    url: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]
    attrs = ["url"]

    def toMarkdown(self) -> str:
        p = self.url.replace('%5C', '\\')
        return rf'![' + ''.join(c.toMarkdown() for c in self.children) + ']' + rf"({p})"

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        oriP = ht.painter().pen()
        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        ht.text(text=self.toMarkdown(), ast=self)

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        s = []
        for c in self.children:
            s += c.segment()
        return [(self, len(self.toMarkdown()))]
