import typing as t

from ..base import MarkdownASTBase
from ...style import MarkdownStyle
from ...abstruct import AbstructCursor, AbstructCachePaint,AbstructTextParagraph


@MarkdownASTBase.registerAst("softbreak")
class SoftBreak(MarkdownASTBase):
    type: str
    propertys = ["type"]

    # to html function
    htmlTag = ""
    content = "\n"

    def toMarkdown(self) -> str:
        return "\n"

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        ht.renderContent(func=AbstructTextParagraph.Render_SoftBreak, ast=self)

    def segment(self) ->t.List[t.Tuple['MarkdownASTBase',int]]:
        return [(self, 0)]


@MarkdownASTBase.registerAst("thematic_break")
class ThematicBreak(MarkdownASTBase):
    type: str
    propertys = ["type"]

    # to html function
    htmlTag = ""
    content = "\n"

    def toMarkdown(self) -> str:
        return "---\n"

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        ht.painter().setFont(style.hintFont(font=ht.painter().font(), ast="blank_line"))

        if isShowHide:
            ht.renderContent(func=AbstructTextParagraph.Render_Text, data=self.toMarkdown(), ast=self)
        else:
            ht.renderContent(func=AbstructTextParagraph.Render_BlankLine, ast=self)
            ht.renderContent(func=AbstructTextParagraph.Render_HideText, data=self.toMarkdown()[:-1], ast=self)
            ht.renderContent(func=AbstructTextParagraph.Render_SoftBreak, ast=self)
        ht.newParagraph()


