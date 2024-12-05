import typing as t

import mistune

from .base import MarkdownASTBase


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


@MarkdownASTBase.registerAst("softbreak")
class SoftBreak(MarkdownASTBase):
    type: str
    propertys = ["type"]

    # to html function
    htmlTag = ""
    content = "\n"

    def toMarkdown(self) -> str:
        return "\n"


@MarkdownASTBase.registerAst("paragraph")
class Paragraph(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]

    # html tag
    htmlTag = "p"

    def toMarkdown(self) -> str:
        return "".join([c.toMarkdown() for c in self.children]) + "\n"


@MarkdownASTBase.registerAst("strong")
class Strong(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]

    # html tag
    htmlTag = "strong"

    def toMarkdown(self) -> str:
        return "*" + "".join([c.toMarkdown() for c in self.children]) + "*"


@MarkdownASTBase.registerAst("emphasis")
class Emphasis(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]

    htmlTag = "em"

    def toMarkdown(self) -> str:
        return "**" + "".join([c.toMarkdown() for c in self.children]) + "**"


@MarkdownASTBase.registerAst("blank_line")
class BlankLine(MarkdownASTBase):
    type: str
    propertys = ["type"]

    htmlTag = ""

    def toMarkdown(self) -> str:
        return "\n"


@MarkdownASTBase.registerAst("list")
class List(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    tight: str
    bullet: str
    depth: int
    ordered: str
    propertys = ["type", "children", "tight", "bullet"]
    attrs = ["depth", "ordered"]

    def htmlTag(self) -> str:
        # print(self.type, self.tight, self.bullet, self.depth, self.ordered)
        return "ol" if self.ordered else "ul"

    def toMarkdown(self) -> str:
        string = ""
        num = 0
        for item in self.children:
            if isinstance(item, ListItem):
                string += "    " * self.depth + (rf"{num}. " if self.ordered else "- ") + item.toMarkdown() + "\n"
            elif isinstance(item, List):
                string += item.toMarkdown()
            else:
                raise Exception()
        return string


@MarkdownASTBase.registerAst("list_item")
class ListItem(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]

    htmlTag = "li"

    def toMarkdown(self) -> str:
        return "".join([c.toMarkdown() for c in self.children])


@MarkdownASTBase.registerAst("block_text")
class BlockText(MarkdownASTBase):
    type: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]

    htmlTag = ""

    def toMarkdown(self) -> str:
        return "".join([c.toMarkdown() for c in self.children])


@MarkdownASTBase.registerAst("text")
class Text(MarkdownASTBase):
    type: str
    raw: str
    propertys = ["type", "raw"]

    # html tag
    htmlTag = ""

    def toMarkdown(self) -> str:
        return self.raw


@MarkdownASTBase.registerAst("block_code")
class BlockCode(MarkdownASTBase):
    type: str
    raw: str
    style: str
    propertys = ["type", "raw", "style"]


@MarkdownASTBase.registerAst("image")
class Image(MarkdownASTBase):
    type: str
    url: str
    children: t.List["MarkdownASTBase"]
    propertys = ["type", "children"]
    attrs = ["url"]

    def toMarkdown(self) -> str:
        p = self.url.replace('%5C','\\')
        return '![img]' + rf"({p})"

from mistune.plugins.math import math
from mistune.plugins.math import math
class MarkdownAst():
    def __init__(self):
        self._text: str = ""

    def setText(self, text: str):
        self._text = text

        # 创建一个 Markdown 解析器
        markdown = mistune.create_markdown(renderer="ast", plugins=[math])
        #markdown = mistune.create_markdown(renderer="ast",plugins=['math'])
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

    def __len__(self):
        return len(self.children)

    def save(self, path):
        markdown_content = "".join([c.toMarkdown() for c in self.children])
        with open(path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

    def addParagraph(self) -> Paragraph:
        """在末尾追加一个 Paragraph"""
        ast_dict = {"type": "paragraph", "children": [{"type": "text", "raw": ""}]}
        paragraph: Paragraph = MarkdownASTBase.createAstFrom(ast_dict["type"])
        paragraph.parseFromAST(ast_dict)
        self.children.append(paragraph)
        return paragraph


if __name__ == "__main__":
    # 创建一个 Markdown 解析器
    markdown = mistune.create_markdown(renderer="ast")

    # Markdown 文本
    markdown_text = \
        """# 这是一个标题
        这是一个段落，带有 **加粗文本** 和 *斜体文本*。
        - 列表项 1
        - 列表项 2
            1. 列表项 3
            2. 列表项 4
        """
    with open("log.md", "r", encoding="utf-8") as f:
        markdown_text = (f.read())
    mdast = MarkdownAst()
    mdast.setText(markdown_text)
    print(mdast.summary())
    print()
    print()
    print(mdast.toHtml())

"""
<h1>项目日志<em><strong>t</strong></em></h1>
<h2>2024.4.7</h2>
<ul>
<li>修复了顶部导航栏，在有moreButton显示时，选中的动画绘制出错的BUG</li>
</ul>
<h2>2024.4.8</h2>
<ul>
<li>添加流程图右侧的节点选择框，还没有实现拖动功能，和自动更新功能</li>
</ul>
<h2>2024.4.9</h2>
<ul>
<li>为流程图右侧的节点选择框添加，拖动功能和自动更新功能</li>
<li>目前流图可以通过拖动获取到对应的QStandItem</li>
</ul>
<p>$$
t=1</p>
<p>$$</p>
<h1>1</h1>
"""
