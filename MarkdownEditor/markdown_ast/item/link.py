import typing as t

from PyQt5.QtCore import Qt

from ..base import MarkdownASTBase
from ...abstruct import AbstructCachePaint
from ...abstruct import AbstructCursor
from ...abstruct import AbstructTextParagraph as ATP
from ...style import MarkdownStyle


@MarkdownASTBase.registerAst("link")
class Link(MarkdownASTBase):
    type: str
    url: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]
    attrs = ["url"]

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

        # ht.text(text=self.toMarkdown(), ast=self)

    def hintCursorShape(self, cursor: AbstructCursor) -> int:
        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        return super(Link, self).hintCursorShape(cursor) if isShowHide else Qt.PointingHandCursor

    def customInteraction(self, cursor: AbstructCursor):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        if isShowHide: return False
        import webbrowser
        # 打开一个 URL
        webbrowser.open(self.url)
        return True
