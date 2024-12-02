import typing as t

from ..base import MarkdownASTBase
from ...component import MarkdownStyle
from ...abstruct import AbstructCursor, AbstructHorizontalText,AbstructTextParagraph


@MarkdownASTBase.registerAst("softbreak")
class SoftBreak(MarkdownASTBase):
    type: str
    propertys = ["type"]

    # to html function
    htmlTag = ""
    content = "\n"

    def toMarkdown(self) -> str:
        return "\n"

    def render(self, ht: AbstructHorizontalText, style: MarkdownStyle, cursor: AbstructCursor = None):
        ht.renderContent(func=AbstructTextParagraph.Render_SoftBreak, ast=self)

    def segment(self) ->t.List[t.Tuple['MarkdownASTBase',int]]:
        return [(self, 0)]
