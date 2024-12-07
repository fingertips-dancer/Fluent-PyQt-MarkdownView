import typing as t

from ..base import MarkdownASTBase
from ...abstruct import AbstructCursor, AbstructCachePaint, AbstructTextParagraph
from ...style import MarkdownStyle


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

    def isShowCollapseButton(self) -> bool:
        return True

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        astName = ("h1","h2","h3","h4","h5","h6")[self.level-1]
        isShowHide = False if cursor is None else cursor.isIn(ast=self)

        ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast=astName, s=self.level))
        if isShowHide:  # 光标
            ht.painter().save()
            ht.painter().setPen(style.hintPen(pen=ht.painter().pen(), ast=astName,pseudo="hidden"))
            ht.renderContent(func=AbstructTextParagraph.Render_Text, data="#" * self.level + " ", ast=self)  # 绘制隐藏项
            ht.painter().restore()
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
