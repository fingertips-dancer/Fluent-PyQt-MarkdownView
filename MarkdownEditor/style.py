import re
import typing as t

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPen, QColor

_global = "global"
default = 'default'
font = 'font'
pen = 'pen'
brush = 'brush'
pointsize = "pointsize"


class MarkdownStyle():
    defaultStyle = {
        default: {pointsize: 20, brush: Qt.NoBrush, pen: Qt.NoPen},
        "header": {}
    }
    fontType = 'Arial'
    headerSize = [36, 34, 32, 30, 28, 26]
    pragraphSize = 20

    @classmethod
    def create(cls, string: str) -> 'MarkdownStyle':
        # 解析 CSS 内容
        import cssutils
        css_parser = cssutils.CSSParser()
        css_sheet = css_parser.parseString(string)

        # 遍历所有规则
        rule_dict = {}
        for rule in css_sheet:
            if rule.type == rule.STYLE_RULE:
                # prase ':'
                if ":" in rule.selectorText:
                    selections, pseudo = rule.selectorText.split(":")
                else:
                    selections, pseudo = rule.selectorText, ""

                # prase ','
                selections = selections.split(",")

                # parse value
                for select in selections:
                    # remove all ’ ‘
                    select = select.strip(" ")
                    # considerate pseudo
                    if pseudo: select = f"{select}:{pseudo}"

                    sub_rule = rule_dict.get(select, {})

                    rule_dict[select] = sub_rule

                    for property in rule.style:
                        value: str = property.value
                        print(select,property.name,property.value)
                        if property.name == "padding":
                            value = tuple([int(e) for e in value.split("px")[:4]])
                        elif property.name == "font-size":
                            value = int(value.strip("px"))
                        elif property.name == "border-width":
                            value = int(value.strip("px"))
                        elif property.name == "color":
                            if property.name.find("rgb") or property.name.find("rgba"):
                                numbers = re.findall(r'\d+', value)  # 使用正则表达式提取所有数字
                                numbers = list(map(int, numbers))  # 将提取出的字符串数字转换为整数
                                value = numbers

                        sub_rule[property.name] = value
        print(rule_dict)
        return MarkdownStyle(rule=rule_dict)

    def _autoToKey(self, ast, pseudo) -> str:
        if pseudo != "":
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

    def hintBackgroundColor(self, ast: str) -> QColor:
        """ 背景颜色 """
        c = QColor(0, 0, 0, 0)
        if ast == "block_math":
            c = QColor(16, 16, 16, 16)

        return c

    def hintBackgroundRadius(self, ast: str) -> float:
        """ 背景圆角半径 """
        c = 15
        return c

    def hintBackgroundMargins(self, ast: str) -> t.Tuple[int, int, int, int]:
        if ast == "block_math":
            return 25, 25, 25, 25
        else:
            return self._rule[ast]["padding"]


if __name__ == "__main__":
    import cssutils

    # 读取 CSS 文件
    css_file = 'E:\study\My-GitHub-Project\Fluent-PyQt-MarkdownView\MarkdownEditor\_rc\github.css'

    with open(css_file, 'r',encoding="utf8") as f:
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
