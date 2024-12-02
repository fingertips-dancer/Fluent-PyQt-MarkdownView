from .abstruct import AbstractMarkDownDocument
from .markdown_ast import MarkdownAstRoot


class MarkDownDocument(AbstractMarkDownDocument):
    def __init__(self):
        super(MarkDownDocument, self).__init__()
        self.markdownAst: MarkdownAstRoot

    def setMarkdown(self, markdown: str, **kwargs) -> None:
        self._text = markdown
        self.__markdownAst = MarkdownAstRoot()
        self.__markdownAst.setText(markdown)
        print(self.__markdownAst.summary())

    def toMarkdown(self) -> str:
        return self.markdownAst.toMarkdown()

    def ast(self) -> MarkdownAstRoot:
        return self.__markdownAst
