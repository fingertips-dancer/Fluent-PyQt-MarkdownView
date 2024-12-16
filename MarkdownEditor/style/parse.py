import re
from typing import Dict, Callable


class Parser():
    parseFunctions = {}

    @classmethod
    def toDict(cls, string: str) -> Dict:
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
                        value = cls.string2Value(name=property.name, string=property.value)
                        sub_rule[property.name] = value
        return rule_dict

    @classmethod
    def string2Value(cls, name, string):
        if name in cls.parseFunctions:
            return cls.parseFunctions[name](string)
        return string

    @classmethod
    def register(cls, name: str):
        def wapper(func: Callable):
            cls.parseFunctions[name] = func
            return func

        return wapper


@Parser.register("padding")
def padding(string: str):
    # 使用 re.findall 查找所有匹配的结果
    matches = re.findall(r'(\d+)px', string)
    ps = tuple(int(t) for t in matches)
    if len(ps) == 4:
        ps = ps
    elif len(ps) == 2:
        ps = ps + ps
    else:
        ps = ps + ps + ps + ps
    return ps


@Parser.register("font-size")
def fontSize(string: str):
    matches = re.findall(r'(\d+)px', string)
    return tuple(int(t) for t in matches)[0]


@Parser.register("border-width")
def borderWidth(string: str):
    matches = re.findall(r'(\d+)px', string)
    return tuple(int(t) for t in matches)[0]


@Parser.register("color")
def color(string: str):
    if string.find("rgb") or string.find("rgba"):
        numbers = re.findall(r'\d+', string)  # 使用正则表达式提取所有数字
        numbers = list(map(int, numbers))  # 将提取出的字符串数字转换为整数
    elif string.find("#"):  # #十六进制
        # 移除可能的 `#` 字符
        hex_color = string.lstrip('#')
        # 将十六进制颜色值转换为 RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        numbers = (r, g, b)
    return numbers


@Parser.register("background-color")
def color(string: str):
    if string.find("rgb") == 0 or string.find("rgba") == 0:
        numbers = re.findall(r'\d+', string)  # 使用正则表达式提取所有数字
        numbers = list(map(int, numbers))  # 将提取出的字符串数字转换为整数
    elif string.find("#") == 0:  # #十六进制
        # 移除可能的 `#` 字符
        hex_color = string.lstrip('#')
        # 将十六进制颜色值转换为 RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        numbers = (r, g, b)
    return numbers


@Parser.register("border-radius")
def borderRadius(string: str):
    matches = re.findall(r'(\d+)px', string)
    if len(matches) == 0:
        matches = re.findall(r'(\d+)', string)

    return tuple(int(t) for t in matches)[0]
