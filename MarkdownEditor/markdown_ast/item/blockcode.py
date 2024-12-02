from ..base import MarkdownASTBase
from ...component import MarkdownStyle
from ...abstruct import AbstructCursor
from ...abstruct import AbstructCachePaint


@MarkdownASTBase.registerAst("block_code")
class BlockCode(MarkdownASTBase):
    type: str
    raw: str
    style: str
    propertys = ["type", "raw", "style"]

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        for c in self.children:
            c.render(ht, style=style, cursor=cursor)
