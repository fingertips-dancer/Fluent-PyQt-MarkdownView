import typing as t

import parse
from PyQt5.QtGui import QFont, QPen, QColor
from functools import cache
from . import utils

nthChildTemplate = parse.compile("nth-child({})")


class MarkdownStyle():
    @classmethod
    def create(cls, string: str) -> 'MarkdownStyle':
        # 解析 CSS 内容
        from .parse import Parser
        rule_dict = Parser.toDict(string)
        print(rule_dict)
        return MarkdownStyle(rule=rule_dict)
    @cache
    def _autoToKey(self, ast, pseudo) -> str:
        # 伪类装饰器
        if pseudo != "":
            # 层叠样式表
            if "nth-child" in pseudo:
                # 选择可能的 nth-child
                partten = f"{ast}:nth-child"
                keys = (k for k in self._rule.keys() if partten in k)
                fr = int(nthChildTemplate.search(pseudo).fixed[0])
                for k in keys:
                    kr_ = nthChildTemplate.search(k).fixed[0]
                    if utils.paserMatch_nth_child(source=kr_, target=fr):
                        pseudo = f'nth-child({kr_})'
                        break
            ast = f"{ast}:{pseudo}"

        if ast not in self._rule:
            ast = 'root'
        return ast

    def __init__(self, rule):
        self._rule = rule

    def inPragraphReutrnSpace(self):
        # 换行间隔
        return 5

    def outPragraphReutrnSpace(self):
        # 段落换行
        return 10

    def hintFont(self, font: QFont, ast: str, pseudo: str = "", **kwargs) -> QFont:
        key = self._autoToKey(ast=ast, pseudo=pseudo)
        sub_rule = self._rule[key]

        if "font-size" in sub_rule:
            font.setPixelSize(sub_rule["font-size"])
        if 'font-family' in sub_rule:
            font.setFamily(sub_rule["font-family"])
        if 'font-style' in sub_rule:
            font.setItalic(sub_rule["font-style"] == "italic")
        if 'font-weight' in sub_rule:
            font.setBold(sub_rule["font-weight"] == "bold")
        return font

    def hintPen(self, pen: QPen, ast: str, pseudo: str = "", **kwargs):
        key = self._autoToKey(ast=ast, pseudo=pseudo)
        sub_rule = self._rule[key]

        if "color" in sub_rule:
            pen.setColor(QColor(*sub_rule["color"]))
        if "border-width" in sub_rule:
            pen.setWidth(sub_rule["border-width"])
        return pen

    def hintIndentation(self, ast: str, **kwargs) -> int:
        """ 推荐缩进 """
        if ast == "block_math":
            indentation = 15
        else:
            indentation = 0
        return indentation

    def hintBackgroundColor(self, ast: str, pseudo: str = "") -> QColor:
        """ 背景颜色 """
        c = QColor(0, 0, 0, 0)
        if ast == "block_math":
            c = QColor(16, 16, 16, 16)

        key = self._autoToKey(ast=ast, pseudo=pseudo)
        sub_rule = self._rule[key]
        if "background-color" in sub_rule:
            c = QColor(*sub_rule["background-color"])

        return c

    def hintBorderRadius(self, ast: str, pseudo: str = "") -> float:
        """ 背景圆角半径 """
        c = 0
        key = self._autoToKey(ast=ast, pseudo=pseudo)
        sub_rule = self._rule[key]
        if "border-radius" in sub_rule:
            c = sub_rule["border-radius"]
        return c

    def hintBackgroundMargins(self, ast: str, pseudo: str = "") -> t.Tuple[int, int, int, int]:
        if ast == "block_math":
            return 25, 25, 25, 25
        padding = (0, 0, 0, 0)
        key = self._autoToKey(ast=ast, pseudo=pseudo)
        sub_rule = self._rule[key]
        if "padding" in sub_rule:
            padding = sub_rule["padding"]
        return padding


if __name__ == "__main__":
    import cssutils

    # 读取 CSS 文件
    css_file = 'E:\study\My-GitHub-Project\Fluent-PyQt-MarkdownView\MarkdownEditor\_rc\github.css'

    with open(css_file, 'r', encoding="utf8") as f:
        css_content = f.read()

    MarkdownStyle.create(css_content)
    # 解析 CSS 内容
    css_parser = cssutils.CSSParser()
    css_sheet = css_parser.parseString(css_content)

    # 遍历所有规则
    for rule in css_sheet:
        if rule.type == rule.STYLE_RULE:
            print(f"Selector: {rule.selectorText}")
            for property in rule.style:
                print(f"  {property.name}: {property.value}")
