import typing as t

from PyQt5.QtGui import QFontMetrics

from ..base import MarkdownASTBase
from ...abstruct import AbstructCursor, AbstructCachePaint, BlockLayer
from ...abstruct import AbstructTextParagraph as ATP
from ...style import MarkdownStyle


@MarkdownASTBase.registerAst("list_item")
class ListItem(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]

    htmlTag = "li"

    def toMarkdown(self) -> str:
        return "".join([c.toMarkdown() for c in self.children])

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        for i, c in enumerate(self.children):
            c.render(ht=ht, style=style, cursor=cursor)
            if not isinstance(c, List):
                ht.renderContent(func=ATP.Render_SoftBreak, ast=self)

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        s = []
        for c in self.children:
            s += c.segment()
        return s


@MarkdownASTBase.registerAst("list")
class List(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    tight: str
    bullet: str
    depth: int
    ordered: str
    start: int = 1
    propertys = ["type", "children", "tight", "bullet"]
    attrs = ["depth", "ordered", "start"]

    def htmlTag(self) -> str:
        # print(self.type, self.tight, self.bullet, self.depth, self.ordered)
        return "ol" if self.ordered else "ul"

    def toMarkdown(self) -> str:
        string = ""
        # 可能是子项
        if self.depth != 0: string += "\n"
        for num, item in enumerate(self.children):
            _string = item.toMarkdown()
            _string += "\n" if len(_string) == 0 or (_string[-1] != "\n") else ""
            string += "    " * self.depth + (rf"{num + 1}. " if self.ordered else "- ") + _string

        return string

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        font = style.hintFont(font=ht.painter().font(), ast="list")
        ht.painter().setFont(font)
        hp = ht.nowParagraph()

        # # 可能是子list
        # if self.depth != 0:
        #     ht.renderContent(func=ATP.Render_SoftBreak, ast=self)
        #     ht.newParagraph()
        layer = BlockLayer()
        for i, c in enumerate(self.children):
            # ph = ht.nowParagraph()
            with ht.newSubParagraph() as sub_ph:
                layer.addItem(sub_ph)
                order_string = "    " * self.depth + (rf"{i + 1}. " if self.ordered else "- ")
                sub_ph.setIndentation(indentation=QFontMetrics(font).width(" " * 3 * min(self.depth, 0) + f"{i + 1}."))
                ht.renderContent(func=ATP.Render_SerialNumber, data=i + 1, ast=self)
                ht.renderContent(func=ATP.Render_HideText, data=order_string, ast=self)
                c.render(ht, style=style, cursor=cursor)

        ht.renderContent(func=ATP.Render_ParagraphLayer, data=layer, ast=self)
        # # 1.换行
        # if self.depth == 0 or i < len(self.children) - 1:
        #     ht.renderContent(func=AbstructTextParagraph.Render_SoftBreak, ast=self)  # 软换行

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        s = []
        for i, c in enumerate(self.children):
            s += [(self, len("    " * self.depth + (rf"{i + 1}. " if self.ordered else "- ")))] + c.segment() + [
                (self, 1)]
        return s
