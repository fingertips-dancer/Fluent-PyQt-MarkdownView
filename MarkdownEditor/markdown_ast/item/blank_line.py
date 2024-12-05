import typing as t

from ..base import MarkdownASTBase
from ...style import MarkdownStyle
from ...abstruct import AbstructCursor, AbstructCachePaint, AbstructTextParagraph


@MarkdownASTBase.registerAst("blank_line")
class BlankLine(MarkdownASTBase):
    type: str
    propertys = ["type"]

    htmlTag = ""

    def toMarkdown(self) -> str:
        return "\n"

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="blank_line"))
        ht.renderContent(func=AbstructTextParagraph.Render_Text, data="\n", ast=self)
        ht.newParagraph()

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        return [(self, 0)]
