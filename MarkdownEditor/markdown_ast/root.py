import typing as t

import mistune
from mistune.plugins.math import math

from .base import MarkdownASTBase
from MarkdownEditor.component.style import MarkdownStyle
from ..abstruct import AbstructCursor, AbstructHorizontalText


class MarkdownAstRoot(MarkdownASTBase):
    def __init__(self):
        self._text: str = ""

    def setText(self, text: str):
        self._text = text

        # 创建一个 Markdown 解析器
        # markdown = mistune.create_markdown(renderer="ast")
        markdown = mistune.create_markdown(renderer="ast", plugins=[math])
        # 解析 Markdown 并获取 AST
        ast = markdown(text)
        self.children = self.parse(ast)

    def parse(self, ast) -> t.List[MarkdownASTBase]:
        children = []
        for sub_ast_dict in ast:
            sub_ast = MarkdownASTBase.createAstFrom(typing=sub_ast_dict["type"])
            sub_ast.parseFromAST(sub_ast_dict)
            setattr(sub_ast, "parent", self)
            children.append(sub_ast)
        return children

    def render(self, ht: AbstructHorizontalText, style: MarkdownStyle, cursor: AbstructCursor = None):
        for c in self.children:
            c.render(ht, style=style, cursor=cursor)

    def __len__(self):
        return len(self.children)

    def save(self, path):
        markdown_content = "".join([c.toMarkdown() for c in self.children])
        with open(path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

    def swap(self, old: t.Union[MarkdownASTBase, t.Tuple[int, int]], new: t.Iterable[MarkdownASTBase]):
        """ 替换"""
        # set parent
        for ast in new: ast.parent = self

        # start and end
        if isinstance(old, MarkdownASTBase):
            idx = self.children.index(old)
            s, e = idx, idx
        elif isinstance(old, tuple) and len(old) == 2:
            s, e = old
        self.children[s:e] = list(new)

    def insert(self, ast: t.Union[MarkdownASTBase, str], idx: int) -> MarkdownASTBase:
        """ 插入 """
        if isinstance(ast, MarkdownASTBase):
            item = ast
        else:
            item = MarkdownASTBase.createAstFrom(ast)
            if ast == "paragraph":
                ast_dict = {"type": "paragraph", "children": [{"type": "text", "raw": ""}]}
            item.parseFromAST(ast_dict)
            item.parent = self
            self.children.insert(idx, item)
        return item

    def summary(self):
        children_str: t.List[str] = []
        for c in self.children:
            children_str.extend(c.summary())
        return "\n".join(children_str)

    def toHtml(self):
        html = "".join([c.toHtml() for c in self.children])

        # 解析 Markdown 并获取 HTML
        md = mistune.create_markdown(renderer="html")
        # html = md(self._text)
        if html[-1] == "\n":
            html = html[:-1]
        return html

    def toMarkdown(self) -> str:
        return "".join([c.toMarkdown() for c in self.children])

    def index(self, ast: MarkdownASTBase) -> int:
        """ the index of children """
        return self.children.index(ast)

    def astOf(self, idx: int) -> MarkdownASTBase:
        """ the child ast of children in idx """
        return self.children[idx]

# markdownAstRoot
