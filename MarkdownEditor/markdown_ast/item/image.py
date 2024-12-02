import typing as t

from ..base import MarkdownASTBase
from ...component import MarkdownStyle
from ...abstruct import AbstructCursor
from ...abstruct import AbstructCachePaint
from ...abstruct import AbstructTextParagraph as ATP


@MarkdownASTBase.registerAst("image")
class Image(MarkdownASTBase):
    type: str
    url: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]
    attrs = ["url"]

    def toMarkdown(self) -> str:
        p = self.url.replace('%5C', '\\')
        return '![img]' + rf"({p})"

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        oriP = ht.painter().pen()
        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        p = self.url.replace('%5C', '\\')

        if isShowHide:
            ht.painter().setPen(style.hintPen(ht.painter().pen(), ast="image"))
            ht.renderContent(func=ATP.Render_Text, data='![img]' + rf"({p})", ast=self)
        else:
            ht.renderContent(func=ATP.Render_HideText, data='![img]' + rf"({p})", ast=self)
            ht.renderContent(func=ATP.Render_Image, data=self.url.replace('%5C', '\\'), ast=self)
        ht.painter().setPen(oriP)  # reset

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        s = []
        for c in self.children:
            s += c.segment()
        return [(self, len(self.toMarkdown()))]
