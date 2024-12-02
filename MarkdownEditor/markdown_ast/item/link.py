import typing as t

from ..base import MarkdownASTBase
from ...component import MarkdownStyle
from ...abstruct import AbstructCursor
from ...abstruct import AbstructCachePaint
from ...abstruct import AbstructTextParagraph as ATP

@MarkdownASTBase.registerAst("link")
class Link(MarkdownASTBase):
    type: str
    url: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]
    attrs = ["url"]

    def toMarkdown(self) -> str:
        return rf'<' + ''.join(c.toMarkdown() for c in self.children) + '>'

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        if isShowHide:
            ht.renderContent(func=ATP.Render_Text, data=self.toMarkdown(), ast=self)
        else:
            ht.renderContent(func=ATP.Render_HideText, data='<', ast=self)
            ht.renderContent(func=ATP.Render_Text, data=''.join(c.toMarkdown() for c in self.children), ast=self)
            ht.renderContent(func=ATP.Render_HideText, data='>', ast=self)
        # ht.text(text=self.toMarkdown(), ast=self)
