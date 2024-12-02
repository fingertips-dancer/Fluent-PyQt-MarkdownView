import typing as t

from ..base import MarkdownASTBase
from ...component import MarkdownStyle
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
        if cursor:
            ast: MarkdownASTBase = cursor.ast()
            if ast is self or ast.isChild(self):
                ht.renderContent(func=AbstructTextParagraph.Render_Text, data="\n", ast=self)
            else:
                ht.renderContent(func=AbstructTextParagraph.Render_BlankLine, ast=self)
                ht.renderContent(func=AbstructTextParagraph.Render_SoftBreak, ast=self)
        else:
            ht.renderContent(func=AbstructTextParagraph.Render_BlankLine, ast=self)
            ht.renderContent(func=AbstructTextParagraph.Render_SoftBreak, ast=self)
        ht.newParagraph()

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        return [(self, 0)]
