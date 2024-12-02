import typing as t

from ..base import MarkdownASTBase
from ...component import MarkdownStyle
from ...abstruct import AbstructCursor, AbstructCachePaint, AbstructTextParagraph


@MarkdownASTBase.registerAst("heading")
class Header(MarkdownASTBase):
    type: str
    level: int
    style: str
    children: t.List["MarkdownASTBase"]

    propertys = ["type", "style", "children"]
    attrs = ["level"]

    # html tag
    def htmlTag(self) -> str:
        return rf"h{self.level}"

    def toMarkdown(self) -> str:
        return "#" * self.level + " " + "".join([c.toMarkdown() for c in self.children]) + "\n"

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        font = style.hintFont(font=ht.painter().font(), ast="header", level=self.level)
        ht.painter().setFont(font)

        if cursor and cursor.ast() is self or cursor.ast().isChild(self):  # 光标
            ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="header", level=self.level, hide=True))
            ht.renderContent(func=AbstructTextParagraph.Render_Text, data="#" * self.level + " ", ast=self)  # 绘制隐藏项
            ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast="header", level=self.level, hide=False))
        else:
            ht.renderContent(func=AbstructTextParagraph.Render_HideText, data="#" * self.level + " ", ast=self)  # 绘制隐藏项

        for c in self.children:
            c.render(ht, style=style, cursor=cursor)
        ht.renderContent(func=AbstructTextParagraph.Render_HardBreak, ast=self)  # 硬换行
        ht.newParagraph()  # 新段落

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        s = []
        for c in self.children:
            s += c.segment()
        return [(self, len("#" * self.level + " "))] + s
