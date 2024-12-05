import typing as t

from ..style import MarkdownStyle
from ..abstruct import AbstructCursor
from ..abstruct import AbstructCachePaint

class MarkdownASTBase():
    __node__ = {}

    # propertys
    children: t.List["MarkdownASTBase"]
    parent: 'MarkdownASTBase'
    type: str
    # ----
    propertys = []
    attrs = []

    # html tag
    htmlTag: t.Union[str, t.Callable]

    @classmethod
    def registerAst(cls, typeStr: str):
        """登记一个节点"""

        def wapper(nodeCls):
            cls.__node__[typeStr] = nodeCls
            return nodeCls

        return wapper

    @classmethod
    def createAstFrom(cls, typing: str) -> 'MarkdownASTBase':
        assert typing in cls.__node__, f"the type <{typing}> is not in {[k for k in cls.__node__.keys()]}"
        return cls.__node__[typing]()

    @classmethod
    def new(cls, ast_dict) -> 'MarkdownASTBase':
        """新建一个节点"""
        sub_ast = MarkdownASTBase.createAstFrom(typing=ast_dict["type"])
        sub_ast.parseFromAST(ast_dict)
        return sub_ast

    def __deepcopy__(self, memodict={}):
        # 创建一个新的对象
        new_copy = type(self)()
        for p in self.propertys:
            if p == "children":
                new_copy.children = [c.__deepcopy__(memodict) for c in self.children]
                [setattr(c, "parent", new_copy) for c in new_copy.children]
            else:
                setattr(new_copy, p, getattr(self, p))
        # attr
        for a in self.attrs:
            setattr(new_copy, a, getattr(self, a))
        # parent
        setattr(new_copy, "parent", self.parent)
        return new_copy

    def parseFromAST(self, ast: dict):
        # property
        for p in self.propertys:
            if p == "children":
                children = []
                for sub_ast_dict in ast.pop("children"):
                    sub_ast = MarkdownASTBase.createAstFrom(typing=sub_ast_dict["type"])
                    sub_ast.parseFromAST(sub_ast_dict)
                    setattr(sub_ast, "parent", self)
                    children.append(sub_ast)
                self.children = children
            else:
                setattr(self, p, ast.pop(p))

        # attr
        if len(self.attrs) != 0:
            attrs = ast.pop("attrs",{})
            for a in self.attrs:
                try:
                    setattr(self, a, attrs.pop(a))
                except KeyError as e:
                    if not hasattr(self,a):
                       raise Exception(f"属性<{a}>没有默认参数, 必须设置")
                except Exception as e:
                    raise e

            assert len(attrs) == 0, f"{self} attrs解析未完成, {[(key,attrs[key]) for key in attrs.keys()]}"
        else:
            assert "attrs" not in ast, f"{self} has attrs: {[(key,ast['attrs'][key]) for key in ast['attrs'].keys()]}"

        assert len(ast) == 0, f"{self} 解析未完成,{[key for key in ast.keys()]}"

    def summary(self) -> t.List[str]:
        my_str = self.toStr()
        children_str: t.List[str] = []
        if hasattr(self, "children"):
            for c in self.children:
                children_str.extend(["    " + string for string in c.summary()])
        return [my_str] + children_str

    def toStr(self) -> str:
        return "".join([f"<{p}>-{getattr(self, p)}  " for p in self.propertys + self.attrs if p != "children"])

    def toHtml(self, lineEnd="\n") -> str:
        """ to html """

        # tag
        assert hasattr(self, "htmlTag"), rf"the {type(self)} - {self.toStr()}"
        if isinstance(self.htmlTag, str):
            tag = self.htmlTag
        else:
            tag = self.htmlTag()

        # content
        if hasattr(self, "children"):
            content = "".join([c.toHtml() for c in self.children])
        elif hasattr(self, "raw"):
            content = getattr(self, "raw")
        elif hasattr(self, "content"):
            if isinstance(self.content, str):
                content = self.content
            else:
                content = self.content()
        else:
            content = ""

        start = "" if tag == "" else rf"<{tag}>"
        end = "" if tag == "" else rf"</{tag}>"

        if getattr(self, "type") == "list":
            return start + "\n" + content + end + lineEnd
        elif getattr(self, "type") in ("strong", "text", "emphasis", "block_text", "blank_line", "softbreak"):
            return start + content + end
        return start + content + end + lineEnd

    def isChild(self, ast: "MarkdownASTBase"):
        """ 是否是子类"""
        while hasattr(ast, "parent"):
            if ast.parent is self:
                return True
            else:  # 子类的子类
                ast = ast.parent
        return False

    def isParent(self, ast: "MarkdownASTBase"):
        """ 是否是父类"""
        possible = ast
        ast = self
        while hasattr(ast, "parent"):
            if ast is possible:
                return True
            else:  # 子类的子类
                ast = ast.parent
        raise Exception
        return False

    def toMarkdown(self) -> str:
        raise NotImplementedError

    def appChildren(self, child: 'MarkdownASTBase'):
        assert hasattr(self, "children"), "the ast node has not children"
        self.children.append(child)

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        raise NotImplementedError(self)

    def segment(self) -> t.List[t.Tuple['MarkdownASTBase', int]]:
        raise NotImplementedError
